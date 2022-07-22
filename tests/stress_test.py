import sys
import os
from time import time as get_time
from generator.domains import Domains
from fastapi.testclient import TestClient
from helpers import check_inspector_response, check_generator_response


TIME_LIMIT = 1


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
    if len(sys.argv) < 3 or sys.argv[1] not in ['inspector', 'generator']:
        print(f'Usage: python {sys.argv[0]} inspector|generator <data file>')
        print(f'Example: python {sys.argv[0]} inspector tests/data/primary.csv')
        exit(1)

    module = sys.argv[1]
    filename = sys.argv[2]

    print('Creating client...')
    client = prod_test_client()

    def run_inspector(name):
        start = get_time()
        resp = client.post('/inspector/', json={'name': name})
        duration = get_time() - start
        assert resp.status_code == 200
        assert duration < TIME_LIMIT, f'Time limit exceeded'
        check_inspector_response(name, resp.json())

    def run_generator(name):
        start = get_time()
        resp = client.post('/', json={'name': name})
        duration = get_time() - start
        assert resp.status_code == 200
        assert duration < TIME_LIMIT, f'Time limit exceeded'
        check_generator_response(resp.json())

    if module == 'inspector':
        stress_test(run_inspector, filename)
    elif module == 'generator':
        stress_test(run_generator, filename)
