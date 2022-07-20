import os
import sys

import pytest
from fastapi.testclient import TestClient

from generator.domains import Domains


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


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_inspector_long_post(prod_test_client):
    client = prod_test_client
    response = client.post("/inspector/",
                           json={"name": "miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan"})

    assert response.status_code == 200

    json = response.json()

    assert 'name' in json
    assert len(json['tokenizations']) == 0


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_inspector_long2_post(prod_test_client):
    client = prod_test_client
    response = client.post("/inspector/", json={"name": "a" * 40000})

    assert response.status_code == 200

    json = response.json()
    assert 'name' in json
    assert len(json['tokenizations']) == 0
