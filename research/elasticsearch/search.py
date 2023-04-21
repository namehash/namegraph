import json
from argparse import ArgumentParser
from math import log10

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
                                "data.collection_name^2",
                                "data.collection_name.exact^3",
                            ],
                            "type": "cross_fields",
                        }
                    }
                ],
                "should": [
                    {
                        "rank_feature": {
                            "field": "template.collection_rank",
                            "boost": 10,
                             "log": {
                                 "scaling_factor": 1
                             }
                        }
                    },
                    {
                        "rank_feature": {
                            "field": "metadata.members_count",
                            "boost": 10,
                             "log": {
                                 "scaling_factor": 1
                             }
                        }
                    }
                ]
            }

        },
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
        valid_ratio = "%.3f" % hit['_source']['template']['valid_members_ratio']
        noavb_count =  hit['_source']['template']['nonavailable_members_count'] 
        noavb_ratio = "%.3f" % hit['_source']['template']['nonavailable_members_ratio']
        is_merged = hit['_source']['template']['is_merged']

        return [score, name, rank, members_value, rank_mean, rank_median, score_mean, score_median, valid_count, valid_ratio, noavb_count, noavb_ratio, is_merged, wikidata_id, type_wikidata_ids, description, keywords, names, ]

    def columns(self):
        return ['score', 'name', 'rank', 'members', 'm. rank mean', 'm. rank median', 'm. int. score mean', 'm. int. score median', 'valid m. count', 'valid m. ratio', 'nonav. count', 'nonav. ratio', 'is merged', 'wikidata', 'types', 'desciption', 'keywords', 'names']

    def __call__(self, query, args):

        body = self.body(query)

        print(f'{body["query"]["bool"]}')

        response = es.search(
            index=INDEX_NAME,
            query=body['query'],
            size=args.limit,
            explain=args.explain
        )

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
        body['query']['bool']['must'][0]['multi_match']['fields'] += [
            "data.collection_types^3",
        ]

        return body


    def header(self):
        return 'name, type, rank'

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
    parser.add_argument('queries', nargs='+', help='queries')
    parser.add_argument('--scheme', default='https', help='elasticsearch scheme')
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--limit', default=10, type=int, help='limit the number of collections to retrieve')
    parser.add_argument('--limit_names', default=100, type=int, help='limit the number of printed names in collections')
    parser.add_argument('--explain', action='store_true', help='run search with explain')
    parser.add_argument('--cloud_id', default=None, help='cloud id')
    args = parser.parse_args()

    if args.cloud_id:
        es = connect_to_elasticsearch_using_cloud_id(args.cloud_id, args.username, args.password)
    else:
        es = connect_to_elasticsearch(args.scheme, args.host, args.port, args.username, args.password)

    print(f'<head><script src="https://cdn.tailwindcss.com"></script></head>')

    for search in [NameTypeSearch(),MemberMeanSearch(),MemberMedianSearch(),ScoreMeanSearch(),ScoreMedianSearch(),ValidRatioSearch(),NonavbRatioSearch()]:
        print(f'<h1 class="px-5 py-2 font-sans text-xl font-bold">{search.description()}</h1>')

        for query in args.queries:
        #for search in [NameRankSearch(), NameSearch(), NameKeywordsDescriptionSearch(), NameMembersSearch()]:
            print(f'<h2 class="px-5 py-2 font-sans text-lg font-bold">{query}</h2>')
            hits = search(query, args)
            print('<table class="m-5">')
            print(f'<tr>')
            for column in search.columns():
                print(f'<th class="sticky bg-blue-300 top-0 border border-slate-300 px-2 py-2">{column}</th>')
            print(f'</tr>')

            for hit in hits:
                print('<tr>')
                for value in search.values(hit, args):
                    print(f'<td class="border border-slate-300 px-2 py-2 text-right">{value}</td>')
                print('</tr>')
            print('</table>')

            if args.explain: print_exlanation(hits)