from argparse import ArgumentParser

from elasticsearch import Elasticsearch
from populate import INDEX_NAME


def connect_to_elasticsearch(
        host: str,
        port: int,
        username: str,
        password: str,
):
    return Elasticsearch(
        hosts=[{
            'scheme': 'http',
            'host': host,
            'port': port
        }],
        http_auth=(username, password)
    )


def search_by_name(query, limit, with_rank=True):
    body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "data.collection_name^2",
                                "data.collection_name.exact^3",
                                "data.collection_description",
                                "data.collection_keywords^2",
                            ],
                            "type": "cross_fields",
                        }
                    }
                ],
                "should": [
                    {
                        "rank_feature": {
                            "field": "template.collection_rank",
                            # "log": {
                            #     "scaling_factor": 4
                            # }
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
        body=body
    )

    hits = response["hits"]["hits"]
    return hits


def search_by_all(query, limit):
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "data.collection_name^2",
                                    "data.collection_name.exact^3",
                                    "data.names.normalized_name",
                                    "data.names.tokenized_name",
                                    "data.collection_description",
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
                                # "log": {
                                #     "scaling_factor": 4
                                # }
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


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('queries', nargs='+', help='queries')
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--limit', default=10, type=int, help='limit the number of collections to retrieve')
    args = parser.parse_args()

    es = connect_to_elasticsearch(args.host, args.port, args.username, args.password)

    for query in args.queries:
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
            type_wikidata_id = hit['_source']['template']['collection_type_wikidata_id']
            wikidata_id = hit['_source']['template']['collection_wikidata_id']
            print(
                f'<tr><td>{score}</td><td><a href="{link}">{name}</a></td><td>{rank}</td><td><a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a></td><td><a href="https://www.wikidata.org/wiki/{type_wikidata_id}">{type_wikidata_id}</a></td></tr>')
        print('</table>')

        print(f'<h2>only collection without rank</h2>')
        hits = search_by_name(query, args.limit, with_rank=False)
        print('<table>')
        print(f'<tr><th>score</th><th>name</th><th>rank</th><th>wikidata</th><th>type</th></tr>')
        for hit in hits:
            score = hit['_score']
            name = hit['_source']['data']['collection_name']
            rank = hit['_source']['template']['collection_rank']
            link = hit['_source']['template']['collection_wikipedia_link']
            type_wikidata_id = hit['_source']['template']['collection_type_wikidata_id']
            wikidata_id = hit['_source']['template']['collection_wikidata_id']
            print(
                f'<tr><td>{score}</td><td><a href="{link}">{name}</a></td><td>{rank}</td><td><a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a></td><td><a href="https://www.wikidata.org/wiki/{type_wikidata_id}">{type_wikidata_id}</a></td></tr>')
        print('</table>')

        print(f'<h2>collection + names</h2>')
        hits = search_by_all(query, args.limit)
        print('<table>')
        print(f'<tr><th>score</th><th>name</th><th>rank</th><th>wikidata</th><th>type</th><th>names</th></tr>')
        for hit in hits:
            score = hit['_score']
            name = hit['_source']['data']['collection_name']
            rank = hit['_source']['template']['collection_rank']
            link = hit['_source']['template']['collection_wikipedia_link']
            type_wikidata_id = hit['_source']['template']['collection_type_wikidata_id']
            wikidata_id = hit['_source']['template']['collection_wikidata_id']
            names = ', '.join([x['normalized_name'] for x in hit['_source']['data']['names']])
            print(
                f'<tr><td>{score}</td><td><a href="{link}">{name}</a></td><td>{rank}</td><td><a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a></td><td><a href="https://www.wikidata.org/wiki/{type_wikidata_id}">{type_wikidata_id}</a></td><td>{names}</td></tr>')

            # print(hit['_score'], hit['_source']['data']['collection_name'], 'RANK:',
            #       hit['_source']['template']['collection_rank'],
            #       hit['_source']['template']['collection_wikipedia_link'])
            # print(', '.join([x['normalized_name'] for x in hit['_source']['data']['names']]))
            print()
        print('</table>')
