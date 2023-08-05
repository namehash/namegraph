import json
from argparse import ArgumentParser
from math import log10
import pprint
import re
import pandas as pd
import numpy as np

from copy import deepcopy

from elasticsearch import Elasticsearch
from populate import INDEX_NAME, connect_to_elasticsearch_using_cloud_id, connect_to_elasticsearch

COMMON_QUERY = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "fields": [
                                "data.collection_name", #1
                                "data.collection_name.exact", #2
                                "data.collection_description", #3
                                "data.collection_keywords", #4
                                "data.names.normalized_name", #5
                                "data.names.tokenized_name", #6
                            ],
                            "type": "most_fields",
                        }
                    }
                ],
                "should": [
                    {
                        "rank_feature": { "field": "template.collection_rank", #7 
                                         "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "metadata.members_rank_mean", #8
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.members_rank_median", #9
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.members_system_interesting_score_mean", #10
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.members_system_interesting_score_median", #11
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.valid_members_count", #12
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.invalid_members_count", #13
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.valid_members_ratio", #14
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.nonavailable_memebers_count", #15
                            "boost": 1, }
                    },
                    {
                        "rank_feature": { "field": "template.nonavailable_memebers_ratio", #16
                            "boost": 1, }
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
                    }
                },
                "query_weight": 0
            }
        }
    }

def print_exlanation(hits):
    print('<details class="m-5"><summary>Explanation</summary><table border=1>')
    for hit in hits:
        name = hit['_source']['data']['collection_name']
        explanation = hit['_explanation']
        explanation = json.dumps(explanation, indent=2, ensure_ascii=False)
        print(f'<tr><td class="font-bold px-5 py-2">{name}</td></tr><tr><td class="px-5 py-2"><pre>{explanation}</pre></td></tr>')
    print('</table></details>')

def is_good_prediction(hits, rf_model, search, args):
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

    return rf_model.predict_proba(df)[:, 1]


class Search:
    def description(self):
        return self.header()

    def values(self, hit, args):
        score = "%.3f" % (hit['_score'] or 0.0)
        data = hit['_source']['data']
        template = hit['_source']['template']

        name = data['collection_name']
        keywords = '; '.join(data['collection_keywords'][:10])
        if len(data['collection_keywords']) > 10:
            keywords += "..."
        description = data['collection_description']
        rank = "%.3f" % log10(template['collection_rank'])
        link = template['collection_wikipedia_link']
        def wikidata_url(id, name):
            return '<a href="https://wikidata.org/wiki/' + str(id) + '">' + str(name) + '</a>'

        type_wikidata_ids = ', '.join([wikidata_url(id, name) for id, name in template['collection_types']])
        names = ', '.join([x['normalized_name'] for x in data['names'][:args.limit_names]])

        if len(data['names']) > args.limit_names:
            names += "..."

        wikidata_id = template['collection_wikidata_id']
        wikidata_id = wikidata_url(wikidata_id, wikidata_id)

        members_count = len(data['names'])
        members_value = f"{members_count} : {'%.3f' % log10(members_count)}"

        rank_mean = "%.1f" % log10(template['members_rank_mean'])
        rank_median = "%.1f" % log10(template['members_rank_median'])
        score_mean = "%.3f" % template['members_system_interesting_score_mean']
        score_median = "%.3f" % template['members_system_interesting_score_median']
        valid_count = template['valid_members_count'] 
        invalid_count = template['invalid_members_count'] 
        valid_ratio = "%.3f" % template['valid_members_ratio']
        noavb_count =  template['nonavailable_members_count'] 
        noavb_ratio = "%.3f" % template['nonavailable_members_ratio']
        is_merged = template['is_merged']

        return [score, name, rank, members_value, rank_mean, rank_median, 
                score_mean, score_median, valid_count, invalid_count, 
                valid_ratio, noavb_count, noavb_ratio, is_merged, 
                wikidata_id, type_wikidata_ids, 
                #description, keywords, 
                names, ]

    def columns(self):
        return ['score', 'name', 'u. score', 'is bad', 'rank', 'members', 'm. rank mean', 'm. rank median', 
                'm. int. score mean', 'm. int. score median', 'valid m. count', 'invalid m. count', 
                'valid m. ratio', 'nonav. count', 'nonav. ratio', 'is merged', 
                'wikidata', 'types', 
                #'desciption', 'keywords', 
                'names']

    def __call__(self, query, args, es):

        body = self.body(query)

        print(f'{body["query"]["bool"]}')
        body['rescore']['query']['rescore_query']['sltr']['model'] = args.ranking_model

        response = es.search(
            index=INDEX_NAME,
            query=body['query'],
            rescore=body['rescore'],
            size=args.limit,
            explain=args.explain
        )

        hits = response["hits"]["hits"]
        return hits

    def key(self):
        return "default"


class AllFieldsSearch(Search):
    def body(self, query):
        body = deepcopy(COMMON_QUERY)
        body['query']['bool']['must'][0]['multi_match']['query'] = query
        body['rescore']['query']['rescore_query']['sltr']['params'] = {"keywords": query}

        return body

    def header(self):
        return 'feature optimization'

    def key(self):
        return "all-fields"

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
    parser.add_argument('--ranking_model', default=None, help='name of the model to re-rank the results')
    parser.add_argument('--scores', default=None, help='file with scores assigned by users (JSONL)')
    parser.add_argument('--imputed_scores', default=None, help='file with relevance scores computed automatically')
    parser.add_argument('--train_results', default=None, help='file with scores on the train dataset')
    parser.add_argument('--test_results', default=None, help='file with scores on the test dataset')

    args = parser.parse_args()

    if args.cloud_id:
        es = connect_to_elasticsearch_using_cloud_id(args.cloud_id, args.username, args.password)
    else:
        es = connect_to_elasticsearch(args.scheme, args.host, args.port, args.username, args.password)

    search_types = {}
    for search in [Search(), AllFieldsSearch()]:
        search_types[search.key()] = search


    rf_model = None
    if args.random_forest_model:
        from joblib import dump, load

        rf_model = load(args.random_forest_model)

    scores = {}
    query_ids = {}
    if args.scores:
        with open(args.scores) as input:
            for idx, row in enumerate(input):
                data = json.loads(row.strip())
                query = list(data.keys())[0]
                scores[query] = {}
                query_ids[idx+1] = query
                for result, score in data[query].items():
                    scores[query][result] = score['user_score']

    testing_results = {}
    baseline_results = {}
    if args.train_results:
        for fname in [args.train_results, args.test_results]:
            with open(fname) as input:
                for row in input:
                    _, id, value = [e for e in row.strip().split(r" ") if len(e) > 0]
                    if(id == 'all'):
                        continue
                    testing_results[query_ids[int(id)]] = float(value)

            fname = re.sub(r"\d+.report$", 'baseline.report', fname)
            with open(fname) as input:
                for row in input:
                    _, id, value = [e for e in row.strip().split(r" ") if len(e) > 0]
                    if(id == 'all'):
                        continue
                    baseline_results[query_ids[int(id)]] = float(value)

    with open(args.output, "w") as output:
        print(f'<head><script src="https://cdn.tailwindcss.com"></script></head>', file=output)

        for search in [AllFieldsSearch()]:

            queries = []
            with open(args.queries) as input:
                for row in input:
                    query = row.strip()
                    value = 0
                    base_value = 0
                    if(query in testing_results):
                        value = testing_results[query]

                    if(query in baseline_results):
                        base_value = baseline_results[query]
                    queries.append((query, value, base_value))

            avg_score = np.average([e[1] for e in  queries])
            avg_base = np.average([e[2] for e in queries])

            delta = f'Δ {"%+.3f" % (avg_score - avg_base)}'
            print(f'<h1 class="px-5 py-2 font-sans text-xl font-bold">{search.description()} ({"%.3f" %avg_score} {delta})</h1>', file=output)


            for query, score, base in sorted(queries, key=lambda x: -x[1]):
                delta = f'Δ {"%+.3f" % (score - base)}'
                print(f'<h2 class="px-5 py-2 font-sans text-lg font-bold">{query} ({"%.3f" %score} {delta} )</h2>', file=output)
                hits = search(query, args, es)
                print('<table class="m-5">', file=output)
                print(f'<tr>', file=output)
                for column in search.columns():
                    print(f'<th class="sticky bg-blue-300 top-0 border border-slate-300 px-2 py-2">{column}</th>', file=output)
                print(f'</tr>', file=output)

                if(rf_model and len(hits) > 0):
                    decision = is_good_prediction(hits, rf_model, search, args)
                else:
                    decision = [0.0] * len(hits)

                for hit, bad_score in zip(hits, decision):
                    if(bad_score > 0.5):
                        print('<tr class="bg-slate-500">', file=output)
                    elif(bad_score > 0.2):
                        print('<tr class="bg-slate-200">', file=output)
                    else:
                        print('<tr>', file=output)

                    # is bad
                    values = search.values(hit, args)
                    values.insert(2, "%.3f" % bad_score)
                    
                    # user score
                    score_value = ""
                    if(query in scores):
                        if(values[1] in scores[query]):
                            score_value = scores[query][values[1]]
                        else:
                            if bad_score > 0.5:
                                scores[query][values[1]] = 0
                            elif bad_score > 0.2:
                                scores[query][values[1]] = 1
                            else:
                                scores[query][values[1]] = 2


                    values.insert(2, score_value)

                    for v_idx, value in enumerate(values):
                        color = ""
                        if(v_idx == 2):
                            if(value is None or len(str(value)) == 0):
                                color = ""
                            elif(value <= 0):
                                color = "bg-red-600"
                            elif(value <= 1):
                                color = "bg-red-300"
                            elif(value <= 2):
                                color = "bg-orange-300"
                            elif(value <= 3):
                                color = "bg-amber-300"
                            elif(value <= 4):
                                color = "bg-lime-300"
                            elif(value <= 5):
                                color = "bg-green-400"

                            if(value is not None and len(str(value)) > 0):
                                value = "%.2f" % float(value)


                        print(f'<td class="border border-slate-300 px-2 py-2 text-right {color}">{value}</td>', file=output)
                    print('</tr>', file=output)
                print('</table>', file=output)

                if args.explain: print_exlanation(hits)

    if args.imputed_scores:
        with open(args.imputed_scores, "w") as imputed_scores:
            for key, values in scores.items():
                converted_values = {}
                for key,value in values.items():
                    converted_values[key] = {'user_score': value}

                imputed_scores.write(json.dumps({key: converted_values}) + "\n")