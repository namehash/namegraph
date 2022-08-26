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
    client.post("/", json={"name": "aaa.eth"})
    return client


@pytest.mark.slow
def test_namehash(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91].eth",
                                      "metadata": False})

    assert response.status_code == 200


@pytest.mark.slow
def test_prod(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "fire", "metadata": False})

    assert response.status_code == 200

    json = response.json()
    str_names = [name["name"] for name in json]
    assert "myfire.eth" in str_names


@pytest.mark.execution_timeout(10)
@pytest.mark.slow
def test_prod_long(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "a" * 40000, "metadata": False})

    assert response.status_code == 200


@pytest.mark.slow
def test_generator_stress(prod_test_client):
    client = prod_test_client
    max_duration = 2
    for name in generate_example_names(400):
        start = get_time()
        response = client.post('/', json={'name': name, "metadata": False})
        duration = get_time() - start
        assert response.status_code == 200, f'{name} failed with {response.status_code}'
        assert duration < max_duration, f'Time exceeded on {name}'


def test_metadata(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "dogcat"})

    assert response.status_code == 200

    json = response.json()
    assert len(json) > 0

    catdog_result = [name for name in json if name["name"] == "catdog.eth"]
    assert len(catdog_result) == 1


@pytest.mark.parametrize(
    "name, min_suggestions, max_suggestions",
    [
        ("tubeyou", 10, 10),  # testing padding using random pipeline
        ("firepower", 50, 100)
    ]
)
def test_min_max_suggestions_parameters(prod_test_client, name: str, min_suggestions: int, max_suggestions: int):
    client = prod_test_client
    response = client.post("/", json={
        "name": name,
        "min_suggestions": min_suggestions,
        "max_suggestions": max_suggestions
    })

    assert response.status_code == 200

    json = response.json()
    unique_names = set([suggestion["name"] for suggestion in json])
    assert len(unique_names) == len(json)

    assert min_suggestions <= len(unique_names)
    assert len(unique_names) <= max_suggestions
