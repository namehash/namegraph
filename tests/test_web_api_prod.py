import os
import sys
from time import time as get_time

import pytest
from fastapi.testclient import TestClient

from generator.domains import Domains

from helpers import check_generator_response, generate_example_names


@pytest.fixture(scope="module")
def prod_test_client():
    Domains.remove_self()
    # TODO override 'generation.wikipedia2vec_path=tests/data/wikipedia2vec.pkl'
    os.environ['CONFIG_NAME'] = 'prod_config'
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.get("/?name=aaa.eth")
    return client


@pytest.mark.slow
def test_get_namehash(prod_test_client):
    client = prod_test_client
    response = client.get("/?name=[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91].eth")

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']


@pytest.mark.slow
def test_prod(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "fire"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "myfire" in primary


@pytest.mark.execution_timeout(10)
@pytest.mark.slow
def test_prod_long(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "a" * 40000})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])


@pytest.mark.execution_timeout(10)
@pytest.mark.slow
def test_prod_long_get(prod_test_client):
    client = prod_test_client
    response = client.get("/?name=" + 'a' * 40000)

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])


@pytest.mark.slow
def test_generator_stress(prod_test_client):
    client = prod_test_client
    max_duration = 2
    for name in generate_example_names(400):
        start = get_time()
        response = client.post('/', json={'name': name})
        duration = get_time() - start
        assert response.status_code == 200, f'{name} failed with {response.status_code}'
        assert duration < max_duration, f'Time exceeded on {name}'
        check_generator_response(response.json())


@pytest.mark.xfail(raises=AssertionError)
def test_metadata(prod_test_client):
    client = prod_test_client
    response = client.post("/metadata", json={"name": "dogcat"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(json.keys()) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert len(primary) > 0
    assert sorted(primary[0].keys()) == sorted(["name", "metadata"])

    catdog_result = [name for name in primary if name["name"] == "catdog"]
    assert len(catdog_result) == 1
