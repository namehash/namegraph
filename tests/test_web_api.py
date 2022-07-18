import os

import pytest
from fastapi.testclient import TestClient

from generator.domains import Domains


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


def test_read_main():
    os.environ['CONFIG_NAME'] = 'test_config'
    import web_api

    client = TestClient(web_api.app)
    response = client.post("/", json={"name": "fire"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "discharge" in primary


def test_get():
    os.environ['CONFIG_NAME'] = 'test_config'
    import web_api

    client = TestClient(web_api.app)
    response = client.get("/?name=firę")

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "discharge" in primary


@pytest.fixture(scope="module")
def prod_test_client():
    # TODO override 'generation.wikipedia2vec_path=tests/data/wikipedia2vec.pkl'
    os.environ['CONFIG_NAME'] = 'prod_config'
    import web_api
    import importlib
    importlib.reload(web_api)
    client = TestClient(web_api.app)
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


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_long(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "a" * 40000})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_long_get(prod_test_client):
    client = prod_test_client
    response = client.get("/?name=" + 'a' * 40000)

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])
