
import json
from argparse import ArgumentParser
from math import log10
import pprint
import re
from tqdm import tqdm
from queue import PriorityQueue
import heapq

from copy import deepcopy

from elasticsearch import Elasticsearch
from search import is_good_prediction, AllFieldsSearch
from populate import INDEX_NAME, connect_to_elasticsearch_using_cloud_id, connect_to_elasticsearch
from dataclasses import dataclass, field
from elasticsearch.helpers import scan
from tqdm import tqdm

@dataclass(order=True)
class PrioritizedItem:
    priority: float
    item: any=field(compare=False)

def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input', help='input file with collections')
    parser.add_argument('--output', help='output file with collections')
    parser.add_argument('--model', help='model used to classify collections')
    parser.add_argument('--limit', default=10, type=int, help='limit the number of collections to retrieve')
    parser.add_argument('--limit_names', default=100, type=int, help='limit the number of printed names in collections')
    parser.add_argument('--explain', action='store_true', help='run search with explain')
    parser.add_argument('--ranking_model', default=None, help='name of the model to re-rank the results')
    args = parser.parse_args()

    
    queue = []
    search = AllFieldsSearch()
    rf_model = None
    if args.model:
        from joblib import dump, load
        rf_model = load(args.model)


    i = 0
    batch = []
    with open(args.input) as input:
        for line in tqdm(input, total=411000):
            hit = json.loads(line.strip())
            hit = {"_source": hit, "_score": 0}
            batch.append(hit)
            if(len(batch) >= 100):
                is_good = is_good_prediction(batch, rf_model, search, args)
                for hit, score in zip(batch, is_good):
                    heapq.heappush(queue, PrioritizedItem(score, hit))
                i += 1
                batch = []

            if(i % 100):
                old_queue = queue
                queue = []
                for i in range(1000):
                    try:
                        heapq.heappush(queue, heapq.heappop(old_queue))
                    except:
                        break

                del old_queue

    with(open(args.output, "w")) as output:
        output.write("<table>\n")
        output.write("<tr>\n")
        output.write('<th>id</th><th>name</th><th>is bad</th><th>type</th><th>valid members count</th><th>valid members ratio</th><th>nonavailable members count</th>' +
        '<th>nonavailable members ratio</th><th>collection name probability</th><th>names</th>\n')
        output.write("</tr>\n")
        for i in range(1000):
            output.write("<tr>\n")
            try:
                item = heapq.heappop(queue)
                data = item.item['_source']['data']
                template = item.item['_source']['template']
                metadata = item.item['_source']['metadata']

                collection_types = template['collection_types']
                types = ', '.join([f'<a href="https://www.wikidata.org/wiki/{x[0]}">{x[1]}</a>' for x in collection_types])
                names = ', '.join([e['normalized_name'] for e in template['top10_names']])

                output.write(f'<td>{metadata["id"]}</td>')
                output.write(f'<td>{data["collection_name"]}</td>')
                output.write(f'<td>{item.priority}</td>')
                output.write(f'<td>{types}</td>')
                output.write(f'<td>{template["valid_members_count"]}</td>')
                output.write(f'<td>{template["valid_members_ratio"]:.2f}</td>')
                output.write(f'<td>{template["nonavailable_members_count"]}</td>')
                output.write(f'<td>{template["nonavailable_members_ratio"]:.2f}</td>')
                output.write(f'<td>{metadata["collection_name_log_probability"]:.2f}</td>')
                output.write(f'<td>{names}</td>')
            except Exception as ex:
                print(ex)
                break
            output.write("</tr>\n")

        output.write("</table>\n")
