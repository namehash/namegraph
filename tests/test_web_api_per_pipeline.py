import os
import sys

import pytest
from pytest import mark
from fastapi.testclient import TestClient

from generator.domains import Domains


@pytest.fixture(scope="module")
def flag_affix_pipeline():
    os.environ['PIPELINES'] = 'test_flag_affix'
    yield
    del os.environ['PIPELINES']


@pytest.fixture(scope="module")
def test_client():
    Domains.remove_self()
    os.environ['CONFIG_NAME'] = 'test_config'
    # import web_api
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.post("/", json={"name": "aaa.eth"})
    return client


@mark.parametrize(
    "name, country, expected_suffix",
    [
        ("metropolis", "ua", "🇺🇦"),
        ("atlantis", "pl", "🇵🇱"),
    ]
)
def test_country_generator_parameter(flag_affix_pipeline, test_client, name: str, country: str, expected_suffix: str):
    client = test_client
    response = client.post("/", json={
        "name": name,
        "params": {
            "generator": {
                "country": country
            }
        }
    })

    assert response.status_code == 200

    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]

    assert any(name.endswith(expected_suffix + '.eth') for name in names)


def test_country_generator_parameter_no_country(flag_affix_pipeline, test_client):
    client = test_client
    name='test'
    country='123'
    
    response = client.post("/", json={
        "name": name,
        "params": {
            "generator": {
                "country": country
            }
        }
    })
    assert response.status_code == 200
    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]
    assert names

    response = client.post("/", json={
        "name": name,
        "params": {
            "generator": {
                "country": '123'
            }
        }
    })
    assert response.status_code == 200
    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]
    assert names

    response = client.post("/", json={
        "name": name,
        "params": {
            "generator": {
                "country": None
            }
        }
    })
    assert response.status_code == 200
    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]
    assert names

    response = client.post("/", json={
        "name": name,
        "params": {
            "generator": {
            }
        }
    })
    assert response.status_code == 200
    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]
    assert names
    
    response = client.post("/", json={
        "name": name,
        "params": {
        }
    })
    assert response.status_code == 200
    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]
    assert names
    
    response = client.post("/", json={
        "name": name,
        "params": None
    })
    assert response.status_code == 200
    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]
    assert names
    
    response = client.post("/", json={
        "name": name,
    })
    assert response.status_code == 200
    json = response.json()
    names: list[str] = [suggestion["name"] for suggestion in json]
    assert names