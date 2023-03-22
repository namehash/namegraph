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


def search_by_name(query, limit):
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["data.collection_name", "data.collection_description",
                                           "data.collection_keywords", ],
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
                                "fields": ["data.collection_name", "data.names.normalized_name",
                                           "data.names.tokenized_name",
                                           "data.collection_description", "data.collection_keywords",
                                           "template.collection_articles"],
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
    parser.add_argument('query', help='query')
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--limit', default=10, type=int, help='limit the number of collections to retrieve')
    args = parser.parse_args()

    es = connect_to_elasticsearch(args.host, args.port, args.username, args.password)

    hits = search_by_name(args.query, args.limit)
    print(f'Results in {INDEX_NAME} - {len(hits)}')

    for hit in hits:
        print(hit['_score'], hit['_source']['data']['collection_name'], 'RANK:',
              hit['_source']['template']['collection_rank'], hit['_source']['template']['collection_wikipedia_link'])

    hits = search_by_all(args.query, args.limit)
    print(f'\nResults in {INDEX_NAME} - {len(hits)}\n')

    for hit in hits:
        print(hit['_score'], hit['_source']['data']['collection_name'], 'RANK:',
              hit['_source']['template']['collection_rank'], hit['_source']['template']['collection_wikipedia_link'])
        print(', '.join([x['normalized_name'] for x in hit['_source']['data']['names']]))
        print()
