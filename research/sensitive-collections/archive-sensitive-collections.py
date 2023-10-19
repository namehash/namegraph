from __future__ import annotations

from argparse import ArgumentParser
import os

from elasticsearch import Elasticsearch


def connect_to_elasticsearch(
        scheme: str,
        host: str,
        port: int,
        username: str,
        password: str,
):
    return Elasticsearch(
        hosts=[{
            'scheme': scheme,
            'host': host,
            'port': port
        }],
        http_auth=(username, password),
        timeout=60,
        http_compress=True,
    )


def archive_collections(es: Elasticsearch, collection_ids: list[str]):
    for collection_id in collection_ids:
        res = es.update(index=index, id=collection_id, body={
            'doc': {
                'data': {
                    'archived': True
                }
            }
        })
        print(res)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='TXT file with collection IDs to archive')
    args = parser.parse_args()

    host = os.getenv('ES_HOST', 'localhost')
    port = int(os.getenv('ES_PORT', '9200'))
    username = os.getenv('ES_USERNAME', 'elastic')
    password = os.getenv('ES_PASSWORD', 'espass')
    index = os.getenv('ES_INDEX', 'collection-templates-1')

    es = connect_to_elasticsearch(
        scheme='http' if host in ['localhost', '127.0.0.1'] else 'https',
        host=host, port=port, username=username, password=password,
    )

    with open(args.input, 'r', encoding='utf-8') as f:
        collection_ids = [line.strip() for line in f.readlines() if line.strip()]

    archive_collections(es, collection_ids)
