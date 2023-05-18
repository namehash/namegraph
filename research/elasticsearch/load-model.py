from argparse import ArgumentParser
from elasticsearch import Elasticsearch
from populate import INDEX_NAME, connect_to_elasticsearch_using_cloud_id, connect_to_elasticsearch
from elasticsearch_ltr import LTRClient
import json
import pprint
import random


FEATURE_SET_NAME="ltr-feature-set"
MODEL_NAME="ltr-model"

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--model', default=None, help='model to load')
    parser.add_argument('--scheme', default='https', help='elasticsearch scheme')
    parser.add_argument('--host', default='localhost', help='elasticsearch hostname')
    parser.add_argument('--port', default=9200, type=int, help='elasticsearch port')
    parser.add_argument('--username', default='elastic', help='elasticsearch username')
    parser.add_argument('--password', default='password', help='elasticsearch password')
    parser.add_argument('--cloud_id', default=None, help='cloud id')
    args = parser.parse_args()

    if(args.model is None):
        print("You have to provide path to the model!")
        exit()

    if args.cloud_id:
        es = connect_to_elasticsearch_using_cloud_id(args.cloud_id, args.username, args.password)
    else:
        es = connect_to_elasticsearch(args.scheme, args.host, args.port, args.username, args.password)

    ltr = LTRClient(es)

    definition = ""
    with open(args.model) as input:
        definition = input.read()

    body = {
        "model": {
            "name": MODEL_NAME,
            "model": {
                "type": "model/ranklib",
                "definition": definition
            }
        }
    }

    ltr.create_model(name=MODEL_NAME, feature_set_name=FEATURE_SET_NAME, body=body)