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


@pytest.mark.slow
def test_prod():
    os.environ['CONFIG_NAME'] = 'prod_config'

    import web_api
    import importlib
    importlib.reload(web_api)

    client = TestClient(web_api.app)
    response = client.post("/", json={"name": "fire"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "myfire" in primary
