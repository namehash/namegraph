import bz2
from argparse import ArgumentParser
from itertools import islice

from pprint import pprint
from typing import Iterable

import jsonlines
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from jsonlines import Reader
from tqdm import tqdm

INDEX_NAME = 'collection-templates-1'


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


def connect_to_elasticsearch_using_cloud_id(
        cloud_id: str,
        username: str,
        password: str,
):
    return Elasticsearch(
        cloud_id=cloud_id,
        basic_auth=(username, password),
        timeout=60,
    )


def initialize_index(es: Elasticsearch):
    # TODO https://github.com/deepset-ai/haystack/blob/main/haystack/document_stores/elasticsearch.py
    # TODO what do all those properties mean? xd https://www.elastic.co/guide/en/elasticsearch/reference/current/text.html
    # mapping = {
    #     'mappings': {
    #         'properties': {
    #             'category':                 {'type': 'text'},
    #             'collection_description':   {'type': 'text'},
    #             'collection_image':         {'type': 'text', 'index': False},
    #             'collection_keywords':      {'type': 'keywords'},
    #             'collection_members':       {'type': 'keywords'},
    #             'collection_name':          {'type': 'text'},
    #             'curated':                  {'type': 'boolean', 'index': False},
    #             'datetime':                 {'type': 'date', 'index': False},
    #             'metadata': {
    #                 'properties': {
    #                     'collection_articles':          {'type': 'keywords'},
    #                     'collection_rank':              {'type': 'rank_feature', 'positive_score_impact': False},
    #                     'collection_type_wikidata_id':  {'type': 'text'},
    #                     'collection_wikidata_id':       {'type': 'text'},
    #                     'collection_wikipedia_link':    {'type': 'text'},
    #                 }
    #             },
    #             'owner':    {'type': 'text', 'index': False},
    #             'public':   {'type': 'boolean'},
    #             'type':     {'type': 'keywords', 'index': False},
    #             'version':  {'type': 'version'}
    #         }
    #     }
    # }
    mapping = None
    mapping = {
        "settings": {
            "number_of_shards": 1,
            "analysis": {
                "analyzer": {
                    "english_stemmer": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "porter_stem"
                        ]
                    },
                    "english_exact": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase"
                        ]
                    }
                }
            },
            "similarity": {
                "BM25_b0": {
                    "type": "BM25",
                    "k1": 1.2,
                    "b": 0
                },
            }
        },
        "mappings": {
            "properties": {
                "data.collection_name": {"type": "text", "similarity": "BM25", "analyzer": "english_stemmer",
                                         "fields": {
                                             "exact": {
                                                 "type": "text",
                                                 "analyzer": "english_exact"
                                             },
                                             "raw": {
                                                 "type": "keyword"
                                             }
                                         }},
                # b=0 so document length doesn't matter
                "data.names.normalized_name": {"type": "text", "similarity": "BM25_b0"},  # keyword?
                "data.names.tokenized_name": {"type": "text", "similarity": "BM25_b0"},
                # "data.collection_description": {"type": "text", "similarity": "BM25"},
                "data.collection_keywords": {"type": "text", "similarity": "BM25"},
                "template.collection_rank": {"type": "rank_feature"},
                "metadata.members_count": {"type": "rank_feature", "fields": {
                    "raw": {
                        "type": "float"
                    }
                }},
                "template.members_rank_mean": {"type": "rank_feature"},
                "template.members_rank_median": {"type": "rank_feature"},
                "template.members_system_interesting_score_mean": {"type": "rank_feature"},
                "template.members_system_interesting_score_median": {"type": "rank_feature"},
                "template.valid_members_count": {"type": "rank_feature"},
                "template.invalid_members_count": {"type": "rank_feature", "positive_score_impact": False},
                "template.valid_members_ratio": {"type": "rank_feature"},
                "template.nonavailable_members_count": {"type": "rank_feature"},
                "template.nonavailable_members_ratio": {"type": "rank_feature", "fields": {
                    "raw": {
                        "type": "float"
                    }
                }},
                "metadata.collection_name_log_probability": {"type": "float"},
            }
        },
    }

    # TODO handle errors
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=mapping)
    else:
        print('Warning: index already exists, no changes applied')


def insert_collection(es: Elasticsearch, collection: dict):
    # TODO handle errors? something else? batching?
    es.index(INDEX_NAME, body=collection)


def insert_collections(es: Elasticsearch, collections: Iterable[dict]):
    number_of_docs = 561000
    progress = tqdm(unit="docs", total=number_of_docs)
    successes = 0

    # create the ES index
    for ok, action in streaming_bulk(client=es,
                                     index=INDEX_NAME,
                                     actions=collections,
                                     max_chunk_bytes=1000000,  # 1MB
                                     # chunk_size=10,
                                     max_retries=1):
        progress.update(1)
        successes += ok
    print("Indexed %d documents" % (successes,))


def gen(path, limit):
    if path.endswith('.jsonl'):
        reader = jsonlines.open(path, 'r')
    elif path.endswith('.bz2'):
        reader = Reader(bz2.open(args.input, "rb"))

    too_long = 0
    for doc in islice(reader.iter(skip_empty=True, skip_invalid=True), limit):
        # rank_feature must be positive

        # if doc['data']['collection_name'].startswith('Lists of'):
        #     continue
        # doc['template']['collection_rank'] = max(1, doc['template']['collection_rank'])  # remove?
        # doc['metadata']['members_count'] = len(doc['data']['names'])

        doc['template']['nonavailable_members_count'] += 1  # TODO?
        doc['template']['invalid_members_count'] += 1  # TODO?

        if doc['metadata']['members_count'] > 10000:
            too_long += 1
            continue

        yield {
            "_index": INDEX_NAME,
            # "_type": '_doc',
            "_source": doc
        }
    print(f'{too_long} collections too long')


if __name__ == '__main__':
    parser = ArgumentParser(description="Insert collections into Elasticsearch")
    parser.add_argument('input', help='input JSONL file with the collections to insert into ES')
    parser.add_argument('--scheme', default='https', help='elasticsearch scheme')
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--limit', default=None, type=int, help='limit the number of collections to insert')
    parser.add_argument('--cloud_id', default=None, help='cloud id')
    args = parser.parse_args()

    if args.cloud_id:
        es = connect_to_elasticsearch_using_cloud_id(args.cloud_id, args.username, args.password)
    else:
        es = connect_to_elasticsearch(args.scheme, args.host, args.port, args.username, args.password)

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)

    initialize_index(es)

    insert_collections(es, gen(args.input, args.limit))

    search = es.search(index=INDEX_NAME, body={'query': {'bool': {}}})
    print(f'Documents overall in {INDEX_NAME} - {len(search["hits"]["hits"])}')
    # 103 collections too long
    # Indexed 424307 documents
