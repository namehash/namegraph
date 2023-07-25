import os
import sys
import json

import pytest
from pytest import mark
from fastapi.testclient import TestClient

from generator.xcollections import CollectionMatcherForAPI, CollectionMatcherForGenerator
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
    client.post("/", json={"label": "aaa.eth"})
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
            "label": name,
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
            "label": name,
            "params": {
                "country": country
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": {
                "country": '123'
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": {
                "country": None
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": {
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": None
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion["name"] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
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
        response = test_client.post("/", json={"label": name})
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
        response = test_client.post("/", json={"label": "fiftysix",
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
        response = test_client.post("/", json={"label": "あかまい"})
        assert response.status_code == 200
        json = response.json()
        names = [name["name"] for name in json]
        assert "akamaihd.eth" in names

    def test_unnormalized(self, test_client):
        response = test_client.post("/", json={"label": "あかまい"})
        assert response.status_code == 200
        json = response.json()
        names = [name["name"] for name in json]
        assert "あかまいhd.eth" in names

    def test_emoji(self, test_client):
        response = test_client.post("/", json={"label": "💛"})
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
        response = test_client.post("/", json={"label": "pinkfloyd"})
        assert response.status_code == 200
        json = response.json()
        collection_names = [name["metadata"]["collection_title"] for name in json]
        assert "Pink Floyd albums" in collection_names
