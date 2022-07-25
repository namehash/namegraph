import sys
import os
import math
from time import time as get_time
from tqdm import tqdm
import argparse

from generator.domains import Domains
from fastapi.testclient import TestClient
from tests.helpers import check_inspector_response, check_generator_response, SPECIAL_CHAR_REGEX


def prod_test_client():
    Domains.remove_self()
    # TODO override 'generation.wikipedia2vec_path=tests/data/wikipedia2vec.pkl'
    os.environ['CONFIG_NAME'] = 'prod_config'
    # TODO lower generator log verbosity
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.get("/?name=aaa.eth")
    return client


def request_inspector(name):
    return client.post('/inspector/', json={'name': name})


def verify_inspector(name, json):
    check_inspector_response(name, json)


def request_generator(name):
    return client.post('/', json={'name': name})


def verify_generator(name, json):
    check_generator_response(json)


def stress_test(fn, filename):
    with open(filename, 'r') as f:
        num_lines = sum(1 for _ in f)
        f.seek(0)

        for i, line in tqdm(enumerate(f), total=num_lines):
            try:
                name = line[:-1]
                fn(name)
            except Exception as e:
                print(f'\n[{i+1}] {name} failed: {e}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-simple', action='store_true', help=f'Skip simple names {SPECIAL_CHAR_REGEX.pattern}')
    parser.add_argument('-t', '--timeout', type=float, default=0, help='Timeout [s] for each request')
    parser.add_argument('-l', '--long-length', type=int, default=500, help='Names above this length will not be skipped')
    parser.add_argument('module', choices=['inspector', 'generator'], help='Module to test')
    parser.add_argument('data_file', help='File with names to use')
    args = parser.parse_args()

    module = args.module
    filename = args.data_file
    timeout = math.inf if args.timeout == 0 else args.timeout
    enable_filter = args.no_simple
    long_length = args.long_length

    print('Creating client...')
    client = prod_test_client()

    request_fn = request_inspector if module == 'inspector' else request_generator
    verify_fn = verify_inspector if module == 'inspector' else verify_generator

    def test_name(name):
        if len(name) < long_length and enable_filter and SPECIAL_CHAR_REGEX.search(name) is None:
            return

        start = get_time()
        resp = request_fn(name)
        duration = get_time() - start
        
        assert resp.status_code == 200
        assert duration < timeout, f'Time limit exceeded'
        
        verify_fn(name, resp.json())

    stress_test(test_name, filename)
