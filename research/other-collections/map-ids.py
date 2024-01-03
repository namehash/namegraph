from argparse import ArgumentParser
import json
import os

from elasticsearch import Elasticsearch, AsyncElasticsearch


def connect_to_elasticsearch(
        scheme: str,
        host: str,
        port: int,
        username: str,
        password: str,
):
    return AsyncElasticsearch(
        hosts=[{
            'scheme': scheme,
            'host': host,
            'port': port
        }],
        http_auth=(username, password),
        timeout=60,
        http_compress=True,
    )


def collect_elastic_ids_for_wikidata_ids(es: Elasticsearch, index: str, wikidata_ids: list[str]) -> dict[str, str]:
    query = {
        'query': {
            'terms': {
                'metadata.id.keyword': wikidata_ids
            }
        },
        '_source': ['metadata.id']
    }
    res = es.search(index=index, body=query, size=len(wikidata_ids))
    return {hit['_source']['metadata']['id']: hit['_id'] for hit in res['hits']['hits']}


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

    wikidata_id2elastic_id = collect_elastic_ids_for_wikidata_ids(
        es, index, [c['id'] for c in other_collections_records]
    )

    mapped_other_collections_records = []
    for record in other_collections_records:
        if not record['id'] in wikidata_id2elastic_id:
            print(f'No elastic ID for {record["id"]} - {record["name"]}')
            continue

        new_record = {
            'id': wikidata_id2elastic_id[record['id']],
            'wikidata_id': record['id'],
            'name': record['name'],
        }
        mapped_other_collections_records.append(new_record)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(mapped_other_collections_records, f, indent=2, ensure_ascii=False)

    # name-generator/data/collections_data/other_collections.json

    # No elastic ID for Q1322417 - Wealthiest historical figures
    # No elastic ID for Q1547772 - Stars for navigation
    # No elastic ID for Q17111813 - Lists of holidays
    # No elastic ID for Q16912543 - Colors
    # No elastic ID for Q6609398 - Child superheroes

    # namehash/lib/client/constants.ts

    # No elastic ID for Q1322417 - Wealthiest historical figures
    # No elastic ID for Q1547772 - Stars for navigation
