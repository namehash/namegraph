from argparse import ArgumentParser
from typing import Any
import json
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


def collect_names_for_elastic_ids(
        es: Elasticsearch,
        index: str,
        elastic_ids: list[str]
) -> dict[str, list[dict[str, Any]]]:

    query = {
        'query': {
            'ids': {
                'values': elastic_ids
            }
        },
        '_source': ['template.top25_names']
    }
    res = es.search(index=index, body=query, size=len(elastic_ids))
    return {
        hit['_id']: hit['_source']['template']['top25_names']
        for hit in res['hits']['hits']
    }


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='Path to the input JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to the output JSON file')
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
        other_collections_records: list[dict[str, str]] = json.load(f)

    elastic_id2names = collect_names_for_elastic_ids(
        es, index, [c['id'] for c in other_collections_records]
    )

    enriched_other_collections_records = []
    for record in other_collections_records:
        if not record['id'] in elastic_id2names:
            print(f'Collection {record["id"]} - {record["name"]} not found')
            continue

        names = elastic_id2names[record['id']]

        new_record = {
            'id': record['id'],
            'wikidata_id': record['id'],
            'name': record['name'],
            'names': [
                {'normalized_name': name['normalized_name'], 'tokenized_name': name['tokenized_name']}
                for name in names
            ]
        }
        enriched_other_collections_records.append(new_record)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(enriched_other_collections_records, f, indent=2, ensure_ascii=False)
