import json
from argparse import ArgumentParser

from elasticsearch import Elasticsearch
from tqdm import tqdm

from populate import INDEX_NAME, connect_to_elasticsearch_using_cloud_id, connect_to_elasticsearch


# INDEX_NAME = 'collections14all'





def search_by_name(query, limit, with_rank=True):
    body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "data.collection_name^3",
                                "data.collection_name.exact^3",
                                "data.collection_description^2",
                                "data.collection_keywords^2",
                                "data.names.normalized_name",
                                "data.names.tokenized_name",
                            ],
                            "type": "cross_fields",
                        }
                    }
                ],
                "should": [
                    {
                        "rank_feature": {
                            "field": "template.collection_rank",
                            "boost": 100,
                            # "log": {
                            #     "scaling_factor": 4
                            # }
                        }
                    },
                    {
                        "rank_feature": {
                            "field": "metadata.members_count",
                        }
                    }
                ]
            }

        },
        "size": limit,
    }
    if not with_rank:
        del body['query']['bool']['should']

    response = es.search(
        index=INDEX_NAME,
        body=body,
        explain=args.explain
    )

    hits = response["hits"]["hits"]
    return hits


def search_by_all(query, limit):
    response = es.search(
        index=INDEX_NAME,
        explain=args.explain,
        body={
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "data.collection_name^3",
                                    "data.collection_name.exact^3",
                                    "data.names.normalized_name",
                                    "data.names.tokenized_name",
                                    "data.collection_description^2",
                                    "data.collection_keywords^2",
                                    # "template.collection_articles"
                                ],
                                "type": "cross_fields",
                            }
                        }
                    ],
                    "should": [
                        {
                            "rank_feature": {
                                "field": "template.collection_rank",
                                "boost": 100,
                                # "log": {
                                #     "scaling_factor": 4
                                # }
                            }
                        },
                        {
                            "rank_feature": {
                                "field": "metadata.members_count",
                            }
                        }
                    ]
                }

            },
            "size": limit,
        },
    )

    hits = response["hits"]["hits"]
    return hits


def print_exlanation(hits):
    print('<details><summary>Explanation</summary><table border=1>')
    print(f'<tr><th>name</th><th>explanation</th></tr>')
    for hit in hits:
        name = hit['_source']['data']['collection_name']
        explanation = hit['_explanation']
        print(
            f'<tr><td>{name}</td><td><pre>{json.dumps(explanation, indent=2, ensure_ascii=False)}</pre></td></tr>')
    print('</table></details>')


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

    for query in tqdm(args.queries):
        print(f'<h1>{query}</h1>')

        print(f'<h2>only collection</h2>')
        hits = search_by_name(query, args.limit)
        print('<table>')
        print(f'<tr><th>score</th><th>name</th><th>rank</th><th>wikidata</th><th>type</th></tr>')
        for hit in hits:
            score = hit['_score']
            name = hit['_source']['data']['collection_name']
            rank = hit['_source']['template']['collection_rank']
            link = hit['_source']['template']['collection_wikipedia_link']
            type_wikidata_ids = hit['_source']['template']['collection_type_wikidata_ids']
            wikidata_id = hit['_source']['template']['collection_wikidata_id']
            print(
                f'<tr><td>{score}</td><td><a href="{link}">{name}</a></td><td>{rank}</td><td><a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a></td><td><a href="https://www.wikidata.org/wiki/{type_wikidata_ids[0]}">{type_wikidata_ids}</a></td></tr>')
        print('</table>')

        if args.explain: print_exlanation(hits)

        print(f'<h2>only collection without rank</h2>')
        hits = search_by_name(query, args.limit, with_rank=False)
        print('<table>')
        print(f'<tr><th>score</th><th>name</th><th>rank</th><th>wikidata</th><th>type</th></tr>')
        for hit in hits:
            score = hit['_score']
            name = hit['_source']['data']['collection_name']
            rank = hit['_source']['template']['collection_rank']
            link = hit['_source']['template']['collection_wikipedia_link']
            type_wikidata_ids = hit['_source']['template']['collection_type_wikidata_ids']
            wikidata_id = hit['_source']['template']['collection_wikidata_id']
            print(
                f'<tr><td>{score}</td><td><a href="{link}">{name}</a></td><td>{rank}</td><td><a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a></td><td><a href="https://www.wikidata.org/wiki/{type_wikidata_ids[0]}">{type_wikidata_ids}</a></td></tr>')
        print('</table>')

        if args.explain: print_exlanation(hits)

        print(f'<h2>collection + names</h2>')
        hits = search_by_all(query, args.limit)
        print('<table>')
        print(f'<tr><th>score</th><th>name</th><th>rank</th><th>wikidata</th><th>type</th><th>names</th></tr>')
        for hit in hits:
            score = hit['_score']
            name = hit['_source']['data']['collection_name']
            rank = hit['_source']['template']['collection_rank']
            link = hit['_source']['template']['collection_wikipedia_link']
            type_wikidata_ids = hit['_source']['template']['collection_type_wikidata_ids']
            wikidata_id = hit['_source']['template']['collection_wikidata_id']
            names = f"<b>{len(hit['_source']['data']['names'])}:</b> " + ', '.join(
                [x['normalized_name'] for x in hit['_source']['data']['names'][:args.limit_names]])
            print(
                f'<tr><td>{score}</td><td><a href="{link}">{name}</a></td><td>{rank}</td><td><a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a></td><td><a href="https://www.wikidata.org/wiki/{type_wikidata_ids[0]}">{type_wikidata_ids}</a></td><td>{names}</td></tr>')

            # print(hit['_score'], hit['_source']['data']['collection_name'], 'RANK:',
            #       hit['_source']['template']['collection_rank'],
            #       hit['_source']['template']['collection_wikipedia_link'])
            # print(', '.join([x['normalized_name'] for x in hit['_source']['data']['names']]))
            print()
        print('</table>')

        if args.explain: print_exlanation(hits)
