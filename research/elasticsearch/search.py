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


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--limit', default=10, type=int, help='limit the number of collections to retrieve')
    args = parser.parse_args()

    es = connect_to_elasticsearch(args.host, args.port, args.username, args.password)

    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": 'mexico',
                    "fields": ["collection_name", "collection_members", "metadata.collection_articles"],
                    "type": "cross_fields",
                }
            },
            "size": args.limit,
        },
    )

    hits = response["hits"]["hits"]
    print(f'Results in {INDEX_NAME} - {len(hits)}\n')

    for hit in hits:
        print(hit['_source']['collection_name'])
        print(', '.join(hit['_source']['collection_members']))
        print()
