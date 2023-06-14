import os
import sys
from time import perf_counter

import pytest
from pytest import mark
from fastapi.testclient import TestClient

from generator.domains import Domains
from generator.generation.categories_generator import Categories


@pytest.fixture(scope="module")
def test_test_client():
    Categories.remove_self()
    Domains.remove_self()
    os.environ['CONFIG_NAME'] = 'test_config_new'
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


@mark.integration_test
def test_collection_api_metadata(test_test_client):
    t0 = perf_counter()

    response = test_test_client.post("/find_collections_by_string", json={
        "query": "australia",
        "mode": "instant",
        "max_related_collections": 5,
        "max_total_collections": 5
    })
    assert response.status_code == 200
    response_json = response.json()
    t1 = perf_counter()

    # total_number_of_related_collections
    assert (response_json['metadata']['total_number_of_related_collections'] >=
            len(response_json['related_collections']))

    # processing_time
    assert response_json['metadata']['processing_time_ms'] <= (t1 - t0) * 1000


@mark.integration_test
def test_collection_api_eth_suffix(test_test_client):
    response = test_test_client.post("/find_collections_by_string", json={
        "query": "australia",
        "mode": "instant",
        "max_related_collections": 5,
        "max_total_collections": 5
    })
    assert response.status_code == 200
    response_json = response.json()
    assert all([member_name['name'].endswith('.eth')
                for collection in response_json['related_collections'] + response_json['other_collections']
                for member_name in collection['names']])


@mark.integration_test
def test_collection_api_membership_count(test_test_client):
    response = test_test_client.post('/get_collections_membership_count', json={'normalized_name': 'opeth'})
    assert response.status_code == 200
    assert response.json()['count'] >= 0