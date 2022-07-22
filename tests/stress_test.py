import sys
import os
import math
from time import time as get_time
import argparse

from generator.domains import Domains
from fastapi.testclient import TestClient
from helpers import check_inspector_response, check_generator_response, SPECIAL_CHAR_REGEX


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


def stress_test(fn, filename):
    with open(filename, 'r') as f:
        num_lines = sum(1 for _ in f)
        f.seek(0)
        print(f'0/{num_lines}')

        for i, line in enumerate(f):
            if (i + 1) % 100 == 0:
                print(f'\r{i+1}/{num_lines}', end='')
            try:
                name = line[:-1]
                fn(name)
            except Exception as e:
                print(f'\n[{i+1}] {name} failed: {e}')

    print(f'\r{num_lines}/{num_lines}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-simple', action='store_true', help='Skip simple names')
    parser.add_argument('-t', type=float, default=0, help='Timeout [s] for each request')
    parser.add_argument('module', choices=['inspector', 'generator'], help='Module to test')
    parser.add_argument('data_file', help='File with names to use')
    args = parser.parse_args()

    module = args.module
    filename = args.data_file
    timeout = math.inf if args.t == 0 else args.t
    enable_filter = args.no_simple

    print('Creating client...')
    client = prod_test_client()

    def run_inspector(name):
        if enable_filter and SPECIAL_CHAR_REGEX.search(name) is None:
            return
        start = get_time()
        resp = client.post('/inspector/', json={'name': name})
        duration = get_time() - start
        assert resp.status_code == 200
        assert duration < timeout, f'Time limit exceeded'
        check_inspector_response(name, resp.json())

    def run_generator(name):
        if enable_filter and SPECIAL_CHAR_REGEX.search(name) is None:
            return
        start = get_time()
        resp = client.post('/', json={'name': name})
        duration = get_time() - start
        assert resp.status_code == 200
        assert duration < timeout, f'Time limit exceeded'
        check_generator_response(resp.json())

    if module == 'inspector':
        stress_test(run_inspector, filename)
    elif module == 'generator':
        stress_test(run_generator, filename)
