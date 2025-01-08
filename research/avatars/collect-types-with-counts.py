from argparse import ArgumentParser
import tqdm
import csv
import os

import elasticsearch
from elasticsearch.helpers import scan

from namegraph.utils.elastic import connect_to_elasticsearch


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--output', type=str, default='types-with-counts.csv', help='output file')
    args = parser.parse_args()

    host = os.environ['ES_HOST']
    port = int(os.environ['ES_PORT'])
    username = os.environ['ES_USERNAME']
    password = os.environ['ES_PASSWORD']
    index = os.environ['ES_INDEX']

    es = connect_to_elasticsearch(
        scheme='https',
        host=host,
        port=port,
        username=username,
        password=password,
    )

    # extract the value of a specific field from all the documents in the index
    # and count the number of documents with each value
    # (this is a very slow operation)
    query = {
        'query': {
            'match_all': {}
        },
        '_source': ['template.collection_types'],
    }

    counts = dict()
    type_id2name = dict()
    for doc in tqdm.tqdm(scan(es, index=index, query=query), total=es.count(index=index)['count']):
        for type_id, type_name in doc['_source']['template']['collection_types']:
            counts[type_id] = counts.get(type_id, 0) + 1
            type_id2name[type_id] = type_name

    # sort the values by their counts
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    # write the results to a CSV file
    with open(args.output, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['type_id', 'type_name', 'count'])
        for type_id, count in sorted_counts:
            writer.writerow([type_id, type_id2name[type_id], count])
