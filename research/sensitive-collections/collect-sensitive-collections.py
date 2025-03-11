from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
import json
import csv
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


@dataclass
class Collection:
    id: str
    name: str
    related_collections: list[Collection]


def search_by_keyword(es: Elasticsearch, keywords: list[str]) -> list[Collection]:
    query = {
        'query': {
            'bool': {
                'should': [
                    {
                        'query_string': {
                            'query': keyword,
                            'fields': ['data.collection_name', 'data.collection_name.exact'],
                            'type': 'cross_fields',
                            'default_operator': 'AND',
                        }
                    }
                    for keyword in keywords
                ]
            }
        },
        '_source': ['data.collection_name', 'name_generator.related_collections']
    }
    res = es.search(index=index, body=query, size=3000)

    collections = []
    for hit in res['hits']['hits']:
        related_collections = []
        if 'name_generator' in hit['_source']:
            for related_collection in hit['_source']['name_generator']['related_collections']:
                related_collections.append(Collection(
                    id=related_collection['collection_id'],
                    name=related_collection['collection_name'],
                    related_collections=[]
                ))

        collections.append(Collection(
            id=hit['_id'],
            name=hit['_source']['data']['collection_name'],
            related_collections=related_collections
        ))
    return collections


if __name__ == '__main__':
    parser = ArgumentParser(description='This scripts takes a list of keywords and searches for collections in '
                                        'Elasticsearch. We then write the result collections and all the related to it '
                                        'collections to a CSV file. We also write a JSON file with name to ID mapping.')
    parser.add_argument('--input', type=str, required=True, help='TXT file with keywords')
    parser.add_argument('--output', type=str, required=True, help='output CSV file')
    parser.add_argument('--mapping-output', type=str, required=True, help='output JSON name to ID mapping file')
    parser.add_argument('--filter-duplicates', action='store_true', help='filter out duplicate collections')
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
        keywords = [line.strip() for line in f.readlines() if line.strip()]

    collections = search_by_keyword(es, keywords)

    mapping = {}
    for collection in collections:
        mapping[collection.name] = collection.id
        for related_collection in collection.related_collections:
            mapping[related_collection.name] = related_collection.id

    with open(args.mapping_output, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    used_collection_ids = set()
    with open(args.output, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        for collection in collections:
            row = []
            if collection.id not in used_collection_ids or not args.filter_duplicates:
                row.append(collection.name)
            else:
                row.append('')
            used_collection_ids.add(collection.id)

            for related_collection in collection.related_collections:
                if related_collection.id not in used_collection_ids or not args.filter_duplicates:
                    row.append(related_collection.name)
                used_collection_ids.add(related_collection.id)

            writer.writerow(row)
