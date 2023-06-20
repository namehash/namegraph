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

    # total_number_of_matched_collections
    number_of_matched = response_json['metadata']['total_number_of_matched_collections']
    if isinstance(number_of_matched, int):
        assert (response_json['metadata']['total_number_of_matched_collections'] >=
                len(response_json['related_collections']))
    else:
        assert number_of_matched == '1000+'

    # processing_time
    es_time = response_json['metadata'].get('elasticsearch_processing_time_ms', None)
    if es_time is None:
        es_time = 0.
    assert es_time <= response_json['metadata']['processing_time_ms'] <= (t1 - t0) * 1000


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

    assert len(response_json['related_collections'] + response_json['other_collections']) <= 5
    assert all([member_name['name'].endswith('.eth')
                for collection in response_json['related_collections'] + response_json['other_collections']
                for member_name in collection['top_names']])


@mark.integration_test
def test_collection_api_membership_count(test_test_client):
    response = test_test_client.post('/count_collections_by_member', json={'label': 'opeth'})
    assert response.status_code == 200
    assert response.json()['count'] >= 0 or response.json()['count'] == '1000+'


# real parameters calls
# instant search
@mark.integration_test
def test_collection_api_instant_search(test_test_client):
    response = test_test_client.post("/find_collections_by_string", json={
        "query": "australia",
        "mode": "instant",
        "max_related_collections": 15,
        "min_other_collections": 0,
        "max_other_collections": 15,
        "max_total_collections": 15,
        "name_diversity_ratio": 0.5,
        "max_per_type": 3,
        "limit_names": 10,
    })

    assert response.status_code == 200
    response_json = response.json()
    print(response_json)


# domain details
@mark.integration_test
def test_collection_api_domain_details(test_test_client):
    response = test_test_client.post("/find_collections_by_string", json={
        "query": "australia",
        "mode": "domain_detail",
        "max_related_collections": 3,
        "min_other_collections": 3,
        "max_other_collections": 3,
        "max_total_collections": 6,
        "name_diversity_ratio": 0.5,
        "max_per_type": 3,
        "limit_names": 10,
    })

    assert response.status_code == 200
    response_json = response.json()
    print(response_json)


# related collections to normalized name
@mark.integration_test
def test_collection_api_domain_details_pagination_by_string(test_test_client):
    response_page_1 = test_test_client.post("/find_collections_by_string", json={
        "query": "canterbury scene progressive rock bands",
        "mode": "domain_detail",
        "min_other_collections": 0,
        "max_other_collections": 0,
        "max_total_collections": 100,
        "name_diversity_ratio": None,  # no diversity
        "max_per_type": None,
        "limit_names": 10,
        "sort_order": 'Z-A',  # sort
        "offset": 0,  # page 1
        "max_related_collections": 100,
    })

    assert response_page_1.status_code == 200
    response_page_1_json = response_page_1.json()

    response_page_2 = test_test_client.post("/find_collections_by_string", json={
        "query": "canterbury scene progressive rock bands",
        "mode": "domain_detail",
        "min_other_collections": 0,
        "max_other_collections": 0,
        "max_total_collections": 100,
        "name_diversity_ratio": None,  # no diversity
        "max_per_type": None,
        "limit_names": 10,
        "sort_order": 'Z-A',  # sort
        "offset": 100,  # page 2
        "max_related_collections": 100,
    })

    assert response_page_2.status_code == 200
    response_page_2_json = response_page_2.json()

    assert response_page_1_json['metadata']['total_number_of_matched_collections'] == '1000+'
    assert response_page_2_json['metadata']['total_number_of_matched_collections'] == '1000+'

    # with no diversity, there shouldn't be any duplicates
    assert all([c1 != c2 for c1 in response_page_1_json['related_collections']
                          for c2 in response_page_2_json['related_collections']])

    # test Z-A sort
    titles = [c['title']
              for c in response_page_1_json['related_collections'] + response_page_2_json['related_collections']]
    assert titles == sorted(titles, reverse=True)


# count membership # TODO: won't be used
@mark.integration_test
def test_collection_api_get_collections_membership_count(test_test_client):
    response = test_test_client.post("/count_collections_by_member", json={
        "label": "australia",
    })

    assert response.status_code == 200
    response_json = response.json()
    print(response_json)
    assert response_json['count'] >= 0 or response_json['count'] == '1000+'

@mark.integration_test
def test_collection_api_get_collections_membership_count_gt_1000(test_test_client):
    response = test_test_client.post("/count_collections_by_member", json={
        "label": "listedbuilding",
    })

    assert response.status_code == 200
    response_json = response.json()
    print(response_json)
    assert response_json['count'] == '1000+'


# membership collections
@mark.integration_test
def test_collection_api_find_collections_by_member_list_az(test_test_client):
    lim = 8
    response = test_test_client.post("/find_collections_by_member", json={
        "label": "australia",
        "sort_order": "A-Z",
        "limit_names": lim,
        "mode": 'domain_detail',
        "offset": 10,
        'max_results': 30
    })

    assert response.status_code == 200
    response_json = response.json()
    collection_list = response_json['collections']

    # test limit names
    assert all([len(c['top_names']) <= lim for c in collection_list])

    # test A-Z sort
    titles = [c['title'] for c in collection_list]
    assert titles == sorted(titles)


@mark.integration_test
def test_collection_api_find_collections_by_member_ai(test_test_client):
    response = test_test_client.post("/find_collections_by_member", json={
        "label": "australia",
        "sort_order": "AI",
        "mode": 'domain_detail',
        "offset": 5,
        'max_results': 10
    })

    assert response.status_code == 200
    response_json = response.json()

    collection_list = response_json['collections']
    titles = [c['title'] for c in collection_list]
    assert any(['Countries' in t for t in titles])


@mark.integration_test
def test_collection_api_find_collections_by_member_page_out_of_bounds(test_test_client):
    response = test_test_client.post("/find_collections_by_member", json={
        "label": "softmachine",
        "mode": "domain_detail",
        "limit_names": 10,
        "sort_order": 'AI',  # sort
        "offset": 20,  # page out of bounds (offset >= n_matched_collections)
        "max_related_collections": 100,
    })

    assert response.status_code == 200
    response_json = response.json()

    assert response_json['metadata']['total_number_of_matched_collections'] <= 20
    assert len(response_json['collections']) == 0  # empty list


# related collections to collection
@mark.integration_test
def test_collection_api_find_collections_by_collection(test_test_client):
    response = test_test_client.post("/find_collections_by_collection", json={
        "collection_id": "Q1510366",
        "max_related_collections": 3,
        "min_other_collections": 0,
        "max_other_collections": 3,
        "max_total_collections": 6,
        "name_diversity_ratio": 0.5,
        "max_per_type": 3,
        "limit_names": 10,
    })

    assert response.status_code == 200
    response_json = response.json()


@mark.integration_test
def test_collection_api_instant_search_dot(test_test_client):
    response = test_test_client.post("/find_collections_by_string", json={
        "query": "australia.eth"
    })
    assert response.status_code == 422


@mark.integration_test
def test_collection_api_member_dot(test_test_client):
    response = test_test_client.post("/find_collections_by_member", json={
        "query": "australia.eth"
    })
    assert response.status_code == 422


@mark.integration_test
def test_collection_api_instant_search_limit_names_gt_10(test_test_client):
    response = test_test_client.post("/find_collections_by_string", json={
        "query": "australia",
        "limit_names": 11,
    })
    assert response.status_code == 422

