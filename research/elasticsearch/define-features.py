from argparse import ArgumentParser
from elasticsearch import Elasticsearch
from populate import INDEX_NAME, connect_to_elasticsearch_using_cloud_id, connect_to_elasticsearch
from elasticsearch_ltr import LTRClient
import json
import pprint
import random
import tqdm

random.seed(0)

FEATURE_SET_NAME="ltr-feature-set"

def rank_feature(feature_field, feature_name=None):
    if feature_name is None:
        feature_name = feature_field[feature_field.rindex(".")+1:]
    return {
            "name": feature_name, 
            "params": [], 
            "template": {
                "rank_feature": {
                    "field": feature_field,
                }
            }
        }

def keyword_feature(feature_field, feature_name=None):
    if feature_name is None:
        feature_name = feature_field[feature_field.rindex(".")+1:]
    return {
        "name": feature_name, 
        "params": ["keywords"], 
        "template": {
            "match": {
                feature_field: "{{keywords}}"
            }
        }
    }

def feature_query(keyword):
    return {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": keyword,
                        "fields": [
                            "data.collection_name",
                            "data.collection_name.exact",
                            "data.names.normalized_name",
                            "data.names.tokenized_name",
                            "data.collection_description",
                            "data.collection_keywords",
                        ],
                        "type": "cross_fields",
                    }
                }
            ],
            "should": [
                {
                    "rank_feature": {
                        "field": "template.collection_rank",
                    }
                },
                {
                    "rank_feature": {
                        "field": "metadata.members_count",
                    }
                },
                {
                    "rank_feature": {
                        "field": "template.members_rank_mean",
                    }
                },
                {
                    "rank_feature": {
                        "field": "template.members_system_interesting_score_median",
                    }
                },
                {
                    "rank_feature": {
                        "field": "template.valid_members_ratio",
                    }
                },
                {
                    "rank_feature": {
                        "field": "template.nonavailable_members_ratio",
                    }
                }
            ],
            "filter": [
                {
                    "sltr": {
                        "_name": "logged_featureset",
                        "featureset": f"{FEATURE_SET_NAME}",
                        "params": {
                            "keywords": keyword
                        }
                    }
                }
            ]
        }
    }


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--scheme', default='https', help='elasticsearch scheme')
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--cloud_id', default=None, help='cloud id')
    parser.add_argument('--reset', default=False, help='if present resets all feature definitions', action='store_true')
    parser.add_argument('--scores', default=None, help='file with relevance scores (JSONL)')
    parser.add_argument('--train', default=None, help='file with output train features (ranklib)')
    parser.add_argument('--test', default=None, help='file with output test features (ranklib)')
    args = parser.parse_args()

    if args.cloud_id:
        es = connect_to_elasticsearch_using_cloud_id(args.cloud_id, args.username, args.password)
    else:
        es = connect_to_elasticsearch(args.scheme, args.host, args.port, args.username, args.password)

    feature_definition = {
        "featureset": {
            "features": [
                keyword_feature("data.collection_name"),
                keyword_feature("data.collection_name.exact"),
                keyword_feature("data.collection_description"),
                keyword_feature("data.collection_keywords"),
                keyword_feature("data.names.normalized_name"),
                keyword_feature("data.names.tokenized_name"),
                rank_feature("template.collection_rank"),
                rank_feature("template.members_rank_mean"),
                rank_feature("template.members_rank_median"),
                rank_feature("template.members_system_interesting_score_mean"),
                rank_feature("template.members_system_interesting_score_median"),
                rank_feature("template.valid_members_count"), 
                rank_feature("template.invalid_members_count"), 
                rank_feature("template.valid_members_ratio"),
                rank_feature("template.nonavailable_members_count"), 
                rank_feature("template.nonavailable_members_ratio"),
                #rank_feature("template.is_merged"),
            ]
        }
    }

    ltr = LTRClient(es)

    feature_sets = ltr.list_feature_sets()
    feature_sets = [e['_source']['name'] for e in feature_sets['hits']['hits']]
    if(FEATURE_SET_NAME not in feature_sets or args.reset):
        ltr.create_feature_set(FEATURE_SET_NAME, json.dumps(feature_definition))
        feature_sets = ltr.list_feature_sets()
        feature_sets = [e['_source']['name'] for e in feature_sets['hits']['hits']]
        assert FEATURE_SET_NAME in feature_sets, f"Failed to create feature set {FEATURE_SET_NAME}"
        print(f"Feature set '{FEATURE_SET_NAME}' created.")
    else:
        print(f"Feature set '{FEATURE_SET_NAME}' already present.")


    ext_query = {
        "ltr_log": {
            "log_specs": {
                "name": "feature_values",
                "named_query": "logged_featureset"
            }
        }
    } 

    train_dataset = []
    test_dataset = []

    with open(args.scores) as input:
        for idx, row in tqdm.tqdm(enumerate(input)):
            data = json.loads(row.strip())
            key = list(data)[0]
            data_package = []


            score_data = data[key]
            scores = {}
            for collection, value in score_data.items():
                scores[collection] = value['user_score']

            result = es.search(query=feature_query(key), ext=ext_query, size=1000)
            for hit in result['hits']['hits']:
                name = hit['_source']['data']['collection_name']
                if(name not in scores):
                    continue
                score = scores[name]

                features = hit['fields']['_ltrlog'][0]['feature_values']

                dataset_row = [str(score), f"qid:{idx+1}"]

                for f_idx, feature in enumerate(features):
                    if 'value' in feature:
                        dataset_row.append(f"{f_idx+1}:{feature['value']}")
                    else:
                        dataset_row.append(f"{f_idx+1}:0.0")

                data_package.append(dataset_row)

            if(random.random() < 0.2):
                test_dataset += data_package
            else:
                train_dataset += data_package


    print(len(train_dataset))
    print(len(test_dataset))

    for name, dataset in [(args.train, train_dataset), (args.test, test_dataset)]:
        with open(name, "w") as output:
            for row in dataset:
                output.write(" ".join(row)+"\n")