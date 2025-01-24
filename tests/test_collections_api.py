import os
import sys
import json
from time import perf_counter

import pytest
from pytest import mark
from fastapi.testclient import TestClient

from namegraph.domains import Domains
from namegraph.generation.categories_generator import Categories
from namegraph.xcollections import CollectionMatcherForAPI, CollectionMatcherForGenerator


@pytest.fixture(scope="class")
def test_test_client():
    Categories.remove_self()
    Domains.remove_self()
    CollectionMatcherForAPI.remove_self()
    CollectionMatcherForGenerator.remove_self()
    os.environ['CONFIG_NAME'] = 'test_config_new'
    # import web_api
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.post("/", json={"label": "aaa"})
    return client


@pytest.fixture(scope="class")
def unavailable_configuration():
    prev_value = os.environ.get('ES_PORT', None)
    os.environ['ES_PORT'] = '9999'
    yield
    os.environ['ES_PORT'] = prev_value


class TestCorrectConfiguration:
    @pytest.mark.integration_test
    def test_elasticsearch_template_collections_search(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "highest mountains",
            "mode": "instant",
            "max_related_collections": 5,
            "max_total_collections": 5
        })

        assert response.status_code == 200
        titles = [collection['title'] for collection in response.json()['related_collections']]
        assert 'Highest mountains on Earth' in titles

    @pytest.mark.integration_test
    def test_elasticsearch_featured_collections_search(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "highestmountains",
            "mode": "instant",
            "max_related_collections": 5,
            "max_total_collections": 5
        })

        assert response.status_code == 200
        titles = [collection['title'] for collection in response.json()['related_collections']]
        assert 'Highest mountains on Earth' in titles

    @mark.integration_test
    def test_collection_api_metadata(self, test_test_client):
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
        es_time = response_json['metadata'].get('elasticsearch_processing_time_ms', 0)
        assert es_time <= response_json['metadata']['processing_time_ms'] <= (t1 - t0) * 1000

    @mark.skip(reason='we return only labels, without the root name')
    @mark.integration_test
    def test_collection_api_eth_suffix(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "australia",
            "mode": "instant",
            "max_related_collections": 5,
            "max_total_collections": 5,
            "min_other_collections": 0,
            "max_other_collections": 0,
            "name_diversity_ratio": None,  # no diversity
            "max_per_type": None,
        })
        assert response.status_code == 200
        response_json = response.json()

        assert len(response_json['related_collections'] + response_json['other_collections']) <= 5
        assert all([member_name['label'].endswith('.eth')
                    for collection in response_json['related_collections'] + response_json['other_collections']
                    for member_name in collection['top_labels']])

    @mark.integration_test
    def test_collection_api_avatar_emojis_and_images(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "australia",
            "max_related_collections": 3,
            "max_total_collections": 6,
            "min_other_collections": 3,
            "max_other_collections": 3
        })
        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

        assert all(
            [not collection['avatar_emoji'].isascii()
             for collection in response_json['related_collections'] + response_json['other_collections']])

        assert all(  # todo: add url validation (?)
            [isinstance(collection['avatar_image'], str) or collection['avatar_image'] is None
             for collection in response_json['related_collections'] + response_json['other_collections']])

    @mark.integration_test
    def test_collection_api_membership_count(self, test_test_client):
        response = test_test_client.post('/count_collections_by_member', json={'label': 'opeth'})
        assert response.status_code == 200
        assert response.json()['count'] >= 0 or response.json()['count'] == '1000+'

    # real parameters calls
    # instant search
    @mark.integration_test
    def test_collection_api_instant_search(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "australia",
            "mode": "instant",
            "max_related_collections": 15,
            "min_other_collections": 0,
            "max_other_collections": 15,
            "max_total_collections": 15,
            "name_diversity_ratio": 0.5,
            "max_per_type": 3,
            "limit_labels": 10,
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    # domain details
    @mark.integration_test
    def test_collection_api_domain_details(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "australia",
            "mode": "domain_detail",
            "max_related_collections": 3,
            "min_other_collections": 3,
            "max_other_collections": 3,
            "max_total_collections": 6,
            "name_diversity_ratio": 0.5,
            "max_per_type": 3,
            "limit_labels": 10,
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    # related collections to normalized name
    @mark.integration_test
    def test_collection_api_domain_details_pagination_by_string(self, test_test_client):
        response_page_1 = test_test_client.post("/find_collections_by_string", json={
            "query": "canterbury scene progressive rock bands",
            "mode": "domain_detail",
            "min_other_collections": 0,
            "max_other_collections": 0,
            "max_total_collections": 100,
            "name_diversity_ratio": None,  # no diversity
            "max_per_type": None,
            "limit_labels": 10,
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
            "limit_labels": 10,
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

    @mark.integration_test
    def test_collection_api_count_by_string(self, test_test_client):
        response = test_test_client.post("/count_collections_by_string", json={
            "query": "australia",
            "mode": "instant"
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    # count membership # TODO: won't be used
    @mark.integration_test
    def test_collection_api_get_collections_membership_count(self, test_test_client):
        response = test_test_client.post("/count_collections_by_member", json={
            "label": "australia",
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)
        assert response_json['count'] >= 0 or response_json['count'] == '1000+'

    @mark.integration_test
    def test_collection_api_get_collections_membership_count_gt_1000(self, test_test_client):
        response = test_test_client.post("/count_collections_by_member", json={
            "label": "listedbuilding",
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)
        assert response_json['count'] == '1000+'

    # membership collections
    @mark.integration_test
    def test_collection_api_find_collections_by_member_list_az(self, test_test_client):
        lim = 8
        response = test_test_client.post("/find_collections_by_member", json={
            "label": "australia",
            "sort_order": "A-Z",
            "limit_labels": lim,
            "mode": 'domain_detail',
            "offset": 10,
            'max_results': 30
        })

        assert response.status_code == 200
        response_json = response.json()
        collection_list = response_json['collections']

        # test limit labels
        assert all([len(c['top_labels']) <= lim for c in collection_list])

        # test A-Z sort
        titles = [c['title'] for c in collection_list]
        assert titles == sorted(titles)

    @mark.integration_test
    def test_collection_api_find_collections_by_member_ai(self, test_test_client):
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
    def test_collection_api_find_collections_by_member_page_out_of_bounds(self, test_test_client):
        response = test_test_client.post("/find_collections_by_member", json={
            "label": "softmachine",
            "mode": "domain_detail",
            "limit_labels": 10,
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
    def test_collection_api_find_collections_by_collection(self, test_test_client):
        response = test_test_client.post("/find_collections_by_collection", json={
            "collection_id": "ri2QqxnAqZT7",  # Q6607079
            "max_related_collections": 10,
            "min_other_collections": 0,
            "max_other_collections": 0,
            "max_total_collections": 10,
            "name_diversity_ratio": 0.5,
            "max_per_type": 3,
            "limit_labels": 10,
            "sort_order": 'Relevance'
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)
        assert 'English people' in [c['title'] for c in response_json['related_collections']]
        assert 'ri2QqxnAqZT7' not in [c['collection_id'] for c in response_json['related_collections']]
        assert len(response_json['related_collections']) == 10


    @mark.integration_test
    def test_collection_api_find_collections_by_collection_az(self, test_test_client):
        response = test_test_client.post("/find_collections_by_collection", json={
            "collection_id": "ri2QqxnAqZT7",  # Q6607079
            "max_related_collections": 8,
            "min_other_collections": 0,
            "max_other_collections": 4,
            "max_total_collections": 10,
            "limit_labels": 6,
            "offset": 8,
            "sort_order": 'A-Z'
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

        collection_list = response_json['related_collections']

        # test limit labels
        assert all([len(c['top_labels']) <= 6 for c in collection_list])

        # test A-Z sort
        titles = [c['title'] for c in collection_list]
        assert titles == sorted(titles)

        # test collection lists length
        assert len(collection_list) <= 8
        assert len(response_json['other_collections']) == min(10 - len(collection_list), 4)

    @mark.integration_test
    def test_collection_api_find_collections_by_collection_not_found(self, test_test_client):
        response = test_test_client.post("/find_collections_by_collection", json={
            "collection_id": "NoSuChId",  # minimal id length is 12
            "max_related_collections": 3,
            "min_other_collections": 0,
            "max_other_collections": 3,
            "max_total_collections": 6,
            "name_diversity_ratio": 0.5,
            "max_per_type": 3,
            "limit_labels": 10,
        })
        assert response.status_code == 404

    @mark.integration_test
    def test_collection_api_instant_search_dot(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "australia.eth"
        })
        assert response.status_code == 422

    @mark.integration_test
    def test_collection_api_member_dot(self, test_test_client):
        response = test_test_client.post("/find_collections_by_member", json={
            "query": "australia.eth"
        })
        assert response.status_code == 422

    @mark.integration_test
    def test_collection_api_instant_search_limit_labels_gt_10(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "australia",
            "limit_labels": 11,
        })
        assert response.status_code == 422

    # invalid field combinations tests
    @mark.integration_test
    def test_collection_api_min_other_le_max_other(self, test_test_client):
        # violated check: min_other_collections <= max_other_collections
        response = test_test_client.post("/find_collections_by_string", json={
            "min_other_collections": 16,
            "max_other_collections": 15,
            "max_related_collections": 20,
            "max_total_collections": 50,
            "query": "australia",
        })

        assert response.status_code == 422

    @mark.integration_test
    def test_collection_api_max_other_le_max_total(self, test_test_client):
        # violated check: max_other_collections <= max_total_collections
        response = test_test_client.post("/find_collections_by_member", json={
            "min_other_collections": 3,
            "max_other_collections": 11,
            "max_related_collections": 5,
            "max_total_collections": 10,
            "query": "australia",
        })

        assert response.status_code == 422

    @mark.integration_test
    def test_collection_api_min_other_plus_max_related_le_max_total(self, test_test_client):
        # violated check: min_other_collections + max_related_collections  <= max_total_collections
        response = test_test_client.post("/find_collections_by_string", json={
            "min_other_collections": 3,
            "max_other_collections": 5,
            "max_related_collections": 8,
            "max_total_collections": 10,
            "query": "australia",
        })

        assert response.status_code == 422

    @mark.integration_test
    def test_collection_api_find_collections_by_string_labelhash_input(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "[59204fd55f432a2d32b0d89aaf9455324dc11671927bedd3d91ce7b7968e5f80]",
            "max_related_collections": 5,
            "min_other_collections": 3,
            "max_other_collections": 5,
            "max_total_collections": 10,
        })

        assert response.status_code == 200
        response_json = response.json()

        # no related collections should be returned for labelhash input
        assert len(response_json['related_collections']) == 0
        # other collections should not be affected by the input type
        assert 3 <= len(response_json['other_collections']) <= 5


    @mark.integration_test
    def test_collection_api_count_collections_by_string_labelhash_input(self, test_test_client):
        response = test_test_client.post("/count_collections_by_string", json={
            "query": "[59204fd55f432a2d32b0d89aaf9455324dc11671927bedd3d91ce7b7968e5f80]",
        })

        assert response.status_code == 200
        response_json = response.json()

        # no related collections should be returned for labelhash input
        assert response_json['count'] == 0


    @mark.integration_test
    def test_collection_api_count_collections_by_member_labelhash_input(self, test_test_client):
        response = test_test_client.post("/count_collections_by_member", json={
            "label": "[59204fd55f432a2d32b0d89aaf9455324dc11671927bedd3d91ce7b7968e5f80]",
        })

        assert response.status_code == 200
        response_json = response.json()

        # no collections should be returned for labelhash input
        assert response_json['count'] == 0


    @mark.integration_test
    def test_collection_api_find_collections_by_member_labelhash_input(self, test_test_client):
        response = test_test_client.post("/find_collections_by_member", json={
            "label": "[59204fd55f432a2d32b0d89aaf9455324dc11671927bedd3d91ce7b7968e5f80]",
            "max_results": 10
        })

        assert response.status_code == 200
        response_json = response.json()

        # no collections should be returned for labelhash input
        assert len(response_json['collections']) == 0


    @pytest.mark.integration_test
    def test_elasticsearch_template_collections_search_tokenization(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "virgilabloh",
            "mode": "instant",
            "max_related_collections": 5,
            "max_total_collections": 5
        })

        assert response.status_code == 200
        titles = [collection['title'] for collection in response.json()['related_collections']]
        print(titles)
        assert 'Industrial designers' in titles
        # assert 'Yu-Gi-Oh! video games' not in titles
        # assert 'Oh Yeon-seo filmography' not in titles

    @pytest.mark.integration_test
    def test_elasticsearch_template_collections_search_tokenization_with_spaces(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "virgil abloh",
            "mode": "instant",
            "max_related_collections": 5,
            "max_total_collections": 5
        })

        assert response.status_code == 200
        titles = [collection['title'] for collection in response.json()['related_collections']]
        print(titles)
        # assert 'Fashion designers' in titles
        assert 'Industrial designers' in titles
        assert 'Yu-Gi-Oh! video games' not in titles
        assert 'Oh Yeon-seo filmography' not in titles

    @mark.integration_test
    def test_fetch_collection_members_pagination(self, test_test_client):
        # Test fetching first page
        response = test_test_client.post("/fetch_collection_members", json={
            "collection_id": "ri2QqxnAqZT7",
            "offset": 0,
            "limit": 10,
            "metadata": True
        })
        assert response.status_code == 200
        response_json = response.json()
        
        assert len(response_json['suggestions']) == 10
        # assert response_json['type'] == 'related'  # we removed this field
        assert response_json['collection_id'] == 'ri2QqxnAqZT7'
        
        # Test fetching second page
        response2 = test_test_client.post("/fetch_collection_members", json={
            "collection_id": "ri2QqxnAqZT7", 
            "offset": 10,
            "limit": 10,
            "metadata": True
        })
        assert response2.status_code == 200
        response2_json = response2.json()
        
        # Verify different pages return different members
        first_page_names = [s['label'] for s in response_json['suggestions']]
        second_page_names = [s['label'] for s in response2_json['suggestions']]
        assert not set(first_page_names).intersection(second_page_names)

    @mark.integration_test
    def test_fetch_collection_members_invalid_id(self, test_test_client):
        response = test_test_client.post("/fetch_collection_members", json={
            "collection_id": "invalid_id",
            "offset": 0,
            "limit": 5,
            "metadata": True
        })
        assert response.status_code == 404
        assert "Collection with id=invalid_id not found" in response.text

    @mark.integration_test
    def test_fetch_collection_members_high_offset(self, test_test_client):
        # Test fetching with very high offset that exceeds collection size
        response = test_test_client.post("/fetch_collection_members", json={
            "collection_id": "ri2QqxnAqZT7",
            "offset": 100000,
            "limit": 10,
            "metadata": True
        })
        assert response.status_code == 200
        response_json = response.json()
        
        # Should return empty suggestions when offset is beyond collection size
        assert len(response_json['suggestions']) == 0

    @mark.integration_test
    def test_fetch_collection_members_tokenized_names(self, test_test_client):
        label2tokens = {
            "dualipa": ("dua", "lipa"),
            "thebeatles": ("the", "beatles"),
            "davidbowie": ("david", "bowie")
        }

        response = test_test_client.post("/fetch_collection_members", json={
            "collection_id": 'ri2QqxnAqZT7',  # Music artists and bands from England
            "offset": 0,
            "limit": 10,
            "metadata": True
        })
        assert response.status_code == 200
        response_json = response.json()
        for item in response_json['suggestions']:
            assert ''.join(item['tokenized_label']) == item['label']
            if item['label'] in label2tokens:
                assert tuple(item['tokenized_label']) == label2tokens[item['label']]

    @mark.integration_test
    def test_get_collection_by_id(self, test_test_client):
        # Test successful retrieval
        response = test_test_client.post("/get_collection_by_id", json={
            "collection_id": "ri2QqxnAqZT7"  # Known collection ID from other tests
        })
        assert response.status_code == 200
        collection = response.json()
        assert collection['collection_id'] == "ri2QqxnAqZT7"
        assert 'title' in collection
        assert 'owner' in collection
        assert 'number_of_labels' in collection
        assert 'last_updated_timestamp' in collection
        assert 'top_labels' in collection
        assert all([tuple(label.keys()) == ('label',) for label in collection['top_labels']])
        assert 'types' in collection
        assert 'avatar_emoji' in collection
        assert 'avatar_image' in collection

        # Test non-existent collection
        response = test_test_client.post("/get_collection_by_id", json={
            "collection_id": "nonexistent_id"
        })
        assert response.status_code == 404
        assert "Collection with id=nonexistent_id not found" in response.text


@mark.usefixtures("unavailable_configuration")
class TestCollectionApiUnavailable:
    @mark.integration_test
    @mark.slow
    def test_collection_api_unavailability_find_collections_by_string(self, test_test_client):
        response = test_test_client.post("/find_collections_by_string", json={
            "query": "highestmountains",
            "mode": "instant",
            "max_related_collections": 5,
            "max_total_collections": 5
        })
        assert response.status_code == 503

    @mark.integration_test
    def test_collection_api_unavailability_find_collections_by_member(self, test_test_client):
        response = test_test_client.post("/find_collections_by_member", json={
            "label": "australia",
            "sort_order": "AI",
            "mode": 'domain_detail',
            "offset": 5,
            'max_results': 10
        })
        assert response.status_code == 503

    @mark.integration_test
    def test_collection_api_unavailability_find_collections_by_collection(self, test_test_client):
        response = test_test_client.post("/find_collections_by_collection", json={
            "collection_id": "ri2QqxnAqZT7",  # Q6607079
            "max_related_collections": 8,
            "min_other_collections": 0,
            "max_other_collections": 2,
            "max_total_collections": 10,
            "limit_labels": 6,
            "offset": 8,
            "sort_order": 'A-Z'
        })
        assert response.status_code == 503

    @mark.integration_test
    def test_collection_api_unavailability_count_collections_by_member(self, test_test_client):
        response = test_test_client.post("/count_collections_by_member", json={
            "label": "australia"
        })
        assert response.status_code == 503

    @mark.integration_test
    def test_get_collection_by_id_unavailable(self, test_test_client):
        response = test_test_client.post("/get_collection_by_id", json={
            "collection_id": "ri2QqxnAqZT7"
        })
        assert response.status_code == 503
        assert "Elasticsearch Unavailable" in response.text