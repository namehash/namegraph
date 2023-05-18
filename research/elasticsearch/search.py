import json
from argparse import ArgumentParser
from math import log10
import pprint

from copy import deepcopy

from elasticsearch import Elasticsearch
from populate import INDEX_NAME, connect_to_elasticsearch_using_cloud_id, connect_to_elasticsearch

MODEL_NAME="ltr-model"


COMMON_QUERY = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "fields": [
                                "data.collection_name^0.24", #1
                                "data.collection_name.exact^0", #2
                                "data.collection_description^0", #3
                                "data.collection_keywords^0.02", #4
                                "data.names.normalized_name^0", #5
                                "data.names.tokenized_name^0.01", #6
                            ],
                            "type": "cross_fields",
                        }
                    }
                ],
                "should": [
                    {
                        "rank_feature": { "field": "template.collection_rank", #7 
                                         "boost": 0, }
                    },
                    {
                        "rank_feature": { "field": "metadata.members_rank_mean", #8
                            "boost": 0.14, }
                    },
                    {
                        "rank_feature": { "field": "template.members_rank_median", #9
                            "boost": 1.26, }
                    },
                    {
                        "rank_feature": { "field": "template.members_system_interesting_score_mean", #10
                            "boost": 0, }
                    },
                    {
                        "rank_feature": { "field": "template.members_system_interesting_score_median", #11
                            "boost": 5.64, }
                    },
                    {
                        "rank_feature": { "field": "template.valid_members_count", #12
                            "boost": 1.9, }
                    },
                    {
                        "rank_feature": { "field": "template.invalid_members_count", #13
                            "boost": 1.7, }
                    },
                    {
                        "rank_feature": { "field": "template.valid_members_ratio", #14
                            "boost": 0, }
                    },
                    {
                        "rank_feature": { "field": "template.nonavailable_memebers_count", #15
                            "boost": 0, }
                    },
                    {
                        "rank_feature": { "field": "template.nonavailable_memebers_ratio", #16
                            "boost": 0, }
                    },
                ]
            }

        },

        "rescore": {
            "window_size": 1000,
            "query": {
                "rescore_query": {
                    "sltr": {
                        "params": {
                            #"keywords": "rambo"
                        },
                        "model": MODEL_NAME
                    }
                }
            }
        }
    }


def search_by_name(query, limit, with_rank=True, with_keyword_description=False):
    body = deepcopy(COMMON_QUERY)
    body['query']['bool']['must'][0]['multi_match']['query'] = query
    if with_keyword_description:
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_description^2",
            "data.collection_keywords^2",
        ]


    print(f'{body["query"]["bool"]}')

    if not with_rank:
        del body['query']['bool']['should']

    response = es.search(
        index=INDEX_NAME,
        query = body['query'],
        size=limit,
        explain=args.explain
    )


    hits = response["hits"]["hits"]
    return hits


def search_by_all(query, limit):
    body = deepcopy(COMMON_QUERY)
    body['query']['bool']['must'][0]['multi_match']['query'] = query
    body['size'] = limit
    body['query']['bool']['must'][0]['multi_match']['fields'] += [
        "data.collection_description^2",
        "data.collection_keywords^2",
        "data.names.normalized_name",
        "data.names.tokenized_name",
    ]

    print(f'{body["query"]["bool"]}')

    response = es.search(
        index=INDEX_NAME,
        query=body['query'],
        size=limit,
        explain=args.explain,
    )

    hits = response["hits"]["hits"]
    return hits


def print_exlanation(hits):
    print('<details class="m-5"><summary>Explanation</summary><table border=1>')
    for hit in hits:
        name = hit['_source']['data']['collection_name']
        explanation = hit['_explanation']
        print(
            f'<tr><td class="font-bold px-5 py-2">{name}</td></tr><tr><td class="px-5 py-2"><pre>{json.dumps(explanation, indent=2, ensure_ascii=False)}</pre></td></tr>')
    print('</table></details>')


class Search:
    def description(self):
        return '<h2 class="px-5 py-2 font-sans text-lg font-bold">%s</h2>' % self.header()

    def values(self, hit, args):
        score = "%.1f" % hit['_score']
        name = hit['_source']['data']['collection_name']
        keywords = '; '.join(hit['_source']['data']['collection_keywords'][:10])
        if len(hit['_source']['data']['collection_keywords']) > 10:
            keywords += "..."
        description = hit['_source']['data']['collection_description']
        rank = "%.3f" % log10(hit['_source']['template']['collection_rank'])
        link = hit['_source']['template']['collection_wikipedia_link']
        type_wikidata_ids = ', '.join(['<a href="https://wikidata.org/wiki/' + id + '">' + name + '</a>' for id, name in hit['_source']['template']['collection_types']])
        #print(hit['_source']['data'])
        names = ', '.join([x['normalized_name'] for x in hit['_source']['data']['names'][:args.limit_names]])

        if len(hit['_source']['data']['names']) > args.limit_names:
            names += "..."

        wikidata_id = hit['_source']['template']['collection_wikidata_id']
        wikidata_id = '<a href="https://wikidata.org/wiki/' + wikidata_id + '">' + wikidata_id + '</a>'

        members_count = len(hit['_source']['data']['names'])
        members_value = f"{members_count} : {'%.3f' % log10(members_count)}"

        rank_mean = "%.1f" % log10(hit['_source']['template']['members_rank_mean'])
        rank_median = "%.1f" % log10(hit['_source']['template']['members_rank_median'])
        score_mean = "%.3f" % hit['_source']['template']['members_system_interesting_score_mean']
        score_median = "%.3f" % hit['_source']['template']['members_system_interesting_score_median']
        valid_count = hit['_source']['template']['valid_members_count'] 
        invalid_count = hit['_source']['template']['invalid_members_count'] 
        valid_ratio = "%.3f" % hit['_source']['template']['valid_members_ratio']
        noavb_count =  hit['_source']['template']['nonavailable_members_count'] 
        noavb_ratio = "%.3f" % hit['_source']['template']['nonavailable_members_ratio']
        is_merged = hit['_source']['template']['is_merged']

        return [score, name, rank, members_value, rank_mean, rank_median, score_mean, score_median, valid_count, invalid_count, valid_ratio, noavb_count, noavb_ratio, is_merged, wikidata_id, type_wikidata_ids, description, keywords, names, ]

    def columns(self):
        return ['score', 'name', 'is bad', 'rank', 'members', 'm. rank mean', 'm. rank median', 'm. int. score mean', 'm. int. score median', 'valid m. count', 'invalid m. count', 'valid m. ratio', 'nonav. count', 'nonav. ratio', 'is merged', 'wikidata', 'types', 'desciption', 'keywords', 'names']

    def __call__(self, query, args):

        body = self.body(query)

        print(f'{body["query"]["bool"]}')

        response = es.search(
            index=INDEX_NAME,
            query=body['query'],
            rescore=body['rescore'],
            size=args.limit,
            explain=args.explain
        )

        print(response['hits']['hits'][0].keys())
        print(response['hits']['total'])
        print(response['hits']['max_score'])

        hits = response["hits"]["hits"]
        return hits


class NameRankSearch(Search):
    def __call__(self, query, args):
        return search_by_name(query, args.limit)

    def header(self):
        return 'name with rank'

class NameSearch(Search):
    def __call__(self, query, args):
        return search_by_name(query, args.limit, with_rank=False)

    def header(self):
        return 'only name without rank'

class NameKeywordsDescriptionSearch(Search):
    def __call__(self, query, args):
        return search_by_name(query, args.limit, with_rank=False, with_keyword_description=True)

    def header(self):
        return 'name, description, keywords without rank'

class NameMembersSearch(Search):
    def __call__(self, query, args):
        return search_by_all(query, args.limit)
    
    def header(self):
        return 'name, description, keywords, members'


class NameTypeSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['rescore']['query']['rescore_query']['sltr']['params'] = {"keywords": query}

        return body


    def header(self):
        return 'optimized linear model'

class MemberMeanSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_types^3",
        ]

        body['query']['bool']['should'] = [
                {
                    "rank_feature": {
                        "field": "template.members_rank_mean",
                        "boost": 10,
                            "log": {
                                "scaling_factor": 1
                            }
                    }
                }
        ]

        return body

    def header(self):
        return 'name, type, mean member rank'


class MemberMedianSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_types^3",
        ]

        body['query']['bool']['should'] = [
                {
                    "rank_feature": {
                        "field": "template.members_rank_median",
                        "boost": 10,
                            "log": {
                                "scaling_factor": 1
                            }
                    }
                }
        ]

        return body

    def header(self):
        return 'name, type, median member rank'

class ScoreMeanSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_types^3",
        ]

        body['query']['bool']['should'] = [
                {
                    "rank_feature": {
                        "field": "template.members_system_interesting_score_mean",
                        "boost": 40,
                            "log": {
                                "scaling_factor": 1
                            }
                    }
                }
        ]

        return body

    def header(self):
        return 'name, type, score mean rank'

class ScoreMedianSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_types^3",
        ]

        body['query']['bool']['should'] = [
                {
                    "rank_feature": {
                        "field": "template.members_system_interesting_score_median",
                        "boost": 40,
                            "log": {
                                "scaling_factor": 1
                            }
                    }
                }
        ]

        return body

    def header(self):
        return 'name, type, score median rank'

class ValidRatioSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_types^3",
        ]

        body['query']['bool']['should'] = [
                {
                    "rank_feature": {
                        "field": "template.valid_members_ratio",
                        "boost": 40,
                            "log": {
                                "scaling_factor": 1
                            }
                    }
                }
        ]

        return body

    def header(self):
        return 'name, type, valid ratio'

class NonavbRatioSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_types^3",
        ]

        body['query']['bool']['should'] = [
                {
                    "rank_feature": {
                        "field": "template.nonavailable_members_ratio",
                        "boost": 40,
                            "log": {
                                "scaling_factor": 1
                            }
                    }
                }
        ]

        return body

    def header(self):
        return 'name, type, nonavailable members ratio'

MemberMedianSearch(),ScoreMeanSearch(),ScoreMedianSearch(),ValidRatioSearch(),NonavbRatioSearch()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--queries', help='file with queries')
    parser.add_argument('--output', default='report.html', help="file with the output report")
    parser.add_argument('--scheme', default='https', help='elasticsearch scheme')
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--limit', default=10, type=int, help='limit the number of collections to retrieve')
    parser.add_argument('--limit_names', default=100, type=int, help='limit the number of printed names in collections')
    parser.add_argument('--explain', action='store_true', help='run search with explain')
    parser.add_argument('--cloud_id', default=None, help='cloud id')
    parser.add_argument('--random_forest_model', default=None, help='random forest model used to filter the results')
    args = parser.parse_args()

    if args.cloud_id:
        es = connect_to_elasticsearch_using_cloud_id(args.cloud_id, args.username, args.password)
    else:
        es = connect_to_elasticsearch(args.scheme, args.host, args.port, args.username, args.password)


    rf_model = None
    if args.random_forest_model:
        from joblib import dump, load
        import pandas as pd
        import numpy as np

        rf_model = load(args.random_forest_model)

    with open(args.output, "w") as output:
        print(f'<head><script src="https://cdn.tailwindcss.com"></script></head>', file=output)

        #for search in [NameTypeSearch(),MemberMeanSearch(),MemberMedianSearch(),ScoreMeanSearch(),ScoreMedianSearch(),ValidRatioSearch(),NonavbRatioSearch()]:
        for search in [NameTypeSearch()]:
            print(f'<h1 class="px-5 py-2 font-sans text-xl font-bold">{search.description()}</h1>', file=output)

            queries = []
            with open(args.queries) as input:
                for row in input:
                    queries.append(row.strip())

            for query in queries:
            #for search in [NameRankSearch(), NameSearch(), NameKeywordsDescriptionSearch(), NameMembersSearch()]:
                print(f'<h2 class="px-5 py-2 font-sans text-lg font-bold">{query}</h2>', file=output)
                hits = search(query, args)
                print('<table class="m-5">', file=output)
                print(f'<tr>', file=output)
                for column in search.columns():
                    print(f'<th class="sticky bg-blue-300 top-0 border border-slate-300 px-2 py-2">{column}</th>', file=output)
                print(f'</tr>', file=output)

                if(rf_model and len(hits) > 0):
                    df = pd.DataFrame(columns=[
                        "rank_log",
                        "mrank_mean_log",
                        "mrank_median_log",
                        "members system interesting score mean",
                        "members system interesting score median",
                        "valid members count",
                        "invalid members count",
                        "valid members ratio",
                        "nonavailable members count",
                        "nonavailable members ratio",
                        "is merged",
                        ])

                    for hit in hits:
                        values = search.values(hit, args) 
                        values = [float(values[2]), *[float(e) for e in values[4:13]], int(values[13])]
                        df.loc[len(df)] = values

                    # change order to match model
                    df = df[["members system interesting score mean",
                        "members system interesting score median",
                        "valid members count",
                        "invalid members count",
                        "valid members ratio",
                        "nonavailable members count",
                        "nonavailable members ratio",
                        "is merged",
                        "rank_log",
                        "mrank_mean_log",
                        "mrank_median_log",]]
                        
                    #df = df.drop(['user_score', 'query', 'elastic_score'], axis=1)

                    decision = rf_model.predict_proba(df)[:, 1]
                else:
                    decision = [0.0] * len(hits)

                for hit, bad_score in zip(hits, decision):
                    if(bad_score > 0.5):
                        print('<tr class="bg-slate-500">', file=output)
                    elif(bad_score > 0.2):
                        print('<tr class="bg-slate-200">', file=output)
                    else:
                        print('<tr>', file=output)

                    values = search.values(hit, args)
                    values.insert(2, "%.3f" % bad_score)
                    for value in values:
                        print(f'<td class="border border-slate-300 px-2 py-2 text-right">{value}</td>', file=output)
                    print('</tr>', file=output)
                print('</table>', file=output)

                if args.explain: print_exlanation(hits)