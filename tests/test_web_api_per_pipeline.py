import os
import sys
import json
from time import perf_counter

import pytest
from pytest import mark
from fastapi.testclient import TestClient

from generator.collection import CollectionMatcher
from generator.domains import Domains
from generator.generation.categories_generator import Categories


@pytest.fixture(scope='class')
def flag_affix_pipeline():
    os.environ['CONFIG_OVERRIDES'] = json.dumps(['pipelines=test_flag_affix'])
    yield
    del os.environ['CONFIG_OVERRIDES']


@pytest.fixture(scope='class')
def emoji_pipeline():
    os.environ['CONFIG_OVERRIDES'] = json.dumps(['pipelines=test_emoji'])
    yield
    del os.environ['CONFIG_OVERRIDES']


@pytest.fixture(scope="class")
def test_client():
    Domains.remove_self()
    Categories.remove_self()
    CollectionMatcher.remove_self()
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


@mark.usefixtures("flag_affix_pipeline")
class TestFlagAffix:
    @mark.parametrize(
        "name, country, expected_suffix",
        [
            ("metropolis", "ua", "🇺🇦"),
            ("atlantis", "pl", "🇵🇱")
        ]
    )
    def test_country_generator_parameter(self, test_client, name: str, country: str, expected_suffix: str):
        client = test_client
        response = client.post("/", json={
            "name": name,
            "params": {
                "country": country
            }
        })

        assert response.status_code == 200

        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]

        assert any(name.endswith(expected_suffix + '.eth') for name in names)

    def test_country_generator_parameter_no_country(self, test_client):
        client = test_client
        name = 'test'
        country = '123'

        response = client.post("/", json={
            "name": name,
            "params": {
                "country": country
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        assert names

        response = client.post("/", json={
            "name": name,
            "params": {
                "country": '123'
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        assert names

        response = client.post("/", json={
            "name": name,
            "params": {
                "country": None
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


@mark.usefixtures("emoji_pipeline")
class TestEmoji:
    @mark.parametrize(
        "name, expected_names",
        [
            ("adoreyoureyes", ["adoreyour👀.eth", "🥰youreyes.eth", "🥰your👀.eth"]),
            ("prayforukraine", ["prayfor🇺🇦.eth", "🙏forukraine.eth", "🙏for🇺🇦.eth"]),
            ("krakowdragon", ["krakow🐉.eth"]),
            ("dragon", ["dragon🐉.eth"])
        ]
    )
    def test_emoji_generator_api(self, test_client, name: str, expected_names: list[str]):
        response = test_client.post("/", json={"name": name})
        assert response.status_code == 200

        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        print(names)

        assert set(expected_names).intersection(names) == set(expected_names)


@pytest.fixture(scope='class')
def only_primary():
    os.environ['CONFIG_OVERRIDES'] = json.dumps(['pipelines=test_hyphen',
                                                 'app.domains=tests/data/suggestable_domains_for_only_primary.csv'])
    yield
    del os.environ['CONFIG_OVERRIDES']


# using hyphen generator we simply can assure which primary names are generated
@mark.usefixtures("only_primary")
class TestOnlyPrimary:
    def test_only_primary_generator_filling_api(self, test_client):
        response = test_client.post("/", json={"name": "fiftysix",
                                               "min_suggestions": 1,
                                               "max_suggestions": 1,
                                               "min_primary_fraction": 1.0})
        assert response.status_code == 200

        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]

        assert len(names) == 1
        assert names[0] in {'glintpay.eth', 'drbaher.eth', '9852222.eth', 'wanadoo.eth',
                            'conio.eth', 'indulgente.eth', 'theclown.eth', 'taco.eth'}


@pytest.fixture(scope='class')
def substring_test_pipeline():
    os.environ['CONFIG_OVERRIDES'] = json.dumps(
        ['pipelines=test_substring',
         'app.domains=tests/data/suggestable_domains_for_substring.csv'])
    yield
    del os.environ['CONFIG_OVERRIDES']


@mark.usefixtures("substring_test_pipeline")
class TestSubstringMatch:
    def test_normalized(self, test_client):
        response = test_client.post("/", json={"name": "あかまい"})
        assert response.status_code == 200
        json = response.json()
        names = [name["name"] for name in json]
        assert "akamaihd.eth" in names

    def test_unnormalized(self, test_client):
        response = test_client.post("/", json={"name": "あかまい"})
        assert response.status_code == 200
        json = response.json()
        names = [name["name"] for name in json]
        assert "あかまいhd.eth" in names

    def test_emoji(self, test_client):
        response = test_client.post("/", json={"name": "💛"})
        assert response.status_code == 200
        json = response.json()
        names = [name["name"] for name in json]
        assert "i💛you.eth" in names


@pytest.fixture(scope='class')
def collection_test_pipelines():
    os.environ['CONFIG_OVERRIDES'] = json.dumps(['pipelines=test_collections'])
    yield
    del os.environ['CONFIG_OVERRIDES']


@mark.usefixtures("collection_test_pipelines")
@mark.integration_test
class TestCollections:
    def test_metadata_collection_field(self, test_client):
        response = test_client.post("/", json={"name": "pinkfloyd"})
        assert response.status_code == 200
        json = response.json()
        collection_names = [name["metadata"]["collection"] for name in json]
        assert "Pink Floyd albums" in collection_names


    #============== collection api tests ==============

    def test_collection_api_metadata(self, test_client):
        t0 = perf_counter()

        response = test_client.post("/find_collections_by_string", json={
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
            assert number_of_matched == '+1000'

        # processing_time
        assert response_json['metadata']['processing_time_ms'] <= (t1 - t0) * 1000


    def test_collection_api_eth_suffix(self, test_client):
        response = test_client.post("/find_collections_by_string", json={
        "query": "australia",
        "mode": "instant",
        "max_related_collections": 5,
        "max_total_collections": 5
    })
        assert response.status_code == 200
        response_json = response.json()
        assert all([member_name['name'].endswith('.eth')
                    for collection in response_json['related_collections'] + response_json['other_collections']
                    for member_name in collection['top_names']])

    def test_collection_api_membership_count(self, test_client):
        response = test_client.post('/count_collections_by_member', json={'label': 'opeth'})
        assert response.status_code == 200
        assert response.json()['count'] >= 0

    # real parameters calls
    # instant search
    def test_collection_api_instant_search(self, test_client):
        response = test_client.post("/find_collections_by_string", json={
            "query": "australia", #without .eth #TODO query can't contain "."
            "mode": "instant",
            "max_related_collections": 15,
            "min_other_collections": 0,
            "max_other_collections": 15,
            "max_total_collections": 15,
            "name_diversity_ratio": 0.5,
            "max_per_type": 3,
            "limit_names": 10, #can't be greater than 10
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    # domain details
    def test_collection_api_domain_details(self, test_client):
        response = test_client.post("/find_collections_by_string", json={
            "query": "australia", #without .eth
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
    def test_collection_api_domain_details_more(self, test_client):
        response = test_client.post("/find_collections_by_string", json={
            "query": "australia", #without .eth
            "mode": "domain_detail",
            "max_related_collections": 100,
            "min_other_collections": 0,
            "max_other_collections": 0,
            "max_total_collections": 100,
            "name_diversity_ratio": 0.0,
            "max_per_type": 3, #TODO: disable
            "limit_names": 10,
            #TODO: add sorting and pagination
            #TODO: maximum number of results should be 1000, if there is more results then return "1000+" in "number_of_names" field
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    # count membership #TODO: won't be used
    def test_collection_api_get_collections_membership_count(self, test_client):
        response = test_client.post("/count_collections_by_member", json={
            "label": "australia", #TODO change name to "label"
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    # memebership collections 
    def test_collection_api_find_collections_membership_list_az(self, test_client):
        response = test_client.post("/find_collections_by_member", json={
            "label": "australia", #without .eth #TODO change name to "label"
            "sort_order": "A-Z",
            #TODO: add mode, pagination, limit_names
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    def test_collection_api_find_collections_membership_list_ai(self, test_client):
        response = test_client.post("/find_collections_by_member", json={
            "label": "australia", #TODO with or without .eth?
            "sort_order": "AI",
            #TODO as above
        })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

    # related collections to collection
    def test_collection_api_find_collections_by_collection(self, test_client):
        response = test_client.post("/find_collections_by_collection", json={
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