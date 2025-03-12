import os
import sys
import json

import pytest
from pytest import mark
from fastapi.testclient import TestClient

from namegraph.xcollections import CollectionMatcherForAPI, CollectionMatcherForGenerator
from namegraph.domains import Domains
from namegraph.generation.categories_generator import Categories


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
    client.post("/", json={"label": "aaa"})
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
        names: list[str] = [suggestion['label'] for suggestion in json]

        assert any(name.endswith(expected_suffix) for name in names)

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
        names: list[str] = [suggestion['label'] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": {
                "country": '123'
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion['label'] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": {
                "country": None
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion['label'] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": {
            }
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion['label'] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
            "params": None
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion['label'] for suggestion in json]
        assert names

        response = client.post("/", json={
            "label": name,
        })
        assert response.status_code == 200
        json = response.json()
        names: list[str] = [suggestion['label'] for suggestion in json]
        assert names

    @mark.parametrize(
        "name, country, expected_suffix",
        [
            ("metropolis", "ua", "🇺🇦"),
            ("atlantis", "pl", "🇵🇱")
        ]
    )
    def test_country_generator_grouped_parameter(self, test_client, name: str, country: str, expected_suffix: str):
        client = test_client
        response = client.post("/suggestions_by_category", json={
            "label": name,
            "params": {
                "user_info": {"user_ip_country": country}
            }
        })
        assert response.status_code == 200

        json = response.json()
        names = [suggestion['label'] for category in json['categories'] for suggestion in category['suggestions']]
        assert any(name.endswith(expected_suffix) for name in names)


@mark.usefixtures("emoji_pipeline")
class TestEmoji:
    @mark.parametrize(
        "name, expected_names",
        [
            ("adoreyoureyes", ["adoreyour👀", "🥰youreyes", "🥰your👀"]),
            ("prayforukraine", ["prayfor🇺🇦", "🙏forukraine", "🙏for🇺🇦"]),
            ("krakowdragon", ["krakow🐉"]),
            ("dragon", ["dragon🐉"])
        ]
    )
    def test_emoji_generator_api(self, test_client, name: str, expected_names: list[str]):
        response = test_client.post("/", json={"label": name})
        assert response.status_code == 200

        json = response.json()
        names: list[str] = [suggestion['label'] for suggestion in json]
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
        names: list[str] = [suggestion['label'] for suggestion in json]

        assert len(names) == 1
        assert names[0] in {'glintpay', 'drbaher', '9852222', 'wanadoo',
                            'conio', 'indulgente', 'theclown', 'taco'}


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
        names = [name['label'] for name in json]
        assert "akamaihd" in names

    def test_unnormalized(self, test_client):
        response = test_client.post("/", json={"label": "あかまい"})
        assert response.status_code == 200
        json = response.json()
        names = [name['label'] for name in json]
        assert "あかまいhd" in names

    def test_emoji(self, test_client):
        response = test_client.post("/", json={"label": "💛"})
        assert response.status_code == 200
        json = response.json()
        names = [name['label'] for name in json]
        assert "i💛you" in names


@pytest.fixture(scope='class')
def collection_test_pipelines():
    os.environ['CONFIG_OVERRIDES'] = json.dumps(['pipelines=test_collections'])
    yield
    del os.environ['CONFIG_OVERRIDES']


@pytest.fixture(scope='class')
def grouped_test_pipelines():
    os.environ['CONFIG_OVERRIDES'] = json.dumps(['pipelines=test_grouped_fast'])
    yield
    del os.environ['CONFIG_OVERRIDES']


def _extract_titles(json_obj: list[dict]) -> list[str]:
    return [name["metadata"]["collection_title"] for name in json_obj]


@mark.usefixtures("collection_test_pipelines")
@mark.integration_test
class TestCollections:
    def test_metadata_collection_field(self, test_client):
        response = test_client.post("/", json={"label": "pinkfloyd"})
        assert response.status_code == 200
        json = response.json()
        collection_names = _extract_titles(json)
        assert "Songs recorded by Pink Floyd" in collection_names

    def test_enabling_learning_to_rank(self, test_client):
        # at least for one of the labels results should be different
        for label in ['pinkfloyd', 'spears', 'kyiv']:
            titles = []
            for enable_ltr in [True, False]:
                response = test_client.post("/", json={
                    "label": label,
                    "params": {"enable_learning_to_rank": enable_ltr}
                })
                assert response.status_code == 200
                json = response.json()
                collection_names = _extract_titles(json)
                titles.append(collection_names)

            for el in titles:
                if el != titles[0]:
                    return

        assert False, "Results are the same for both enable_learning_to_rank=True and enable_learning_to_rank=False"

    def test_metadata_collection_field2(self, test_client):
        response = test_client.post("/", json={"label": "virgil abloh"})
        assert response.status_code == 200
        json = response.json()
        collection_names = _extract_titles(json)
        print(collection_names)
        # assert "Industrial designers" in collection_names
        assert "American people of Ghanaian descent" in collection_names
        assert "Yu-Gi-Oh! video games" not in collection_names
        assert "Oh Yeon-seo filmography" not in collection_names

    def test_prod_grouped_by_category_old(self, test_client):
        client = test_client

        response = client.post("/grouped_by_category",
                               json={"label": "virgil abloh", "min_suggestions": 100, "max_suggestions": 100,
                                     "metadata": True,
                                     "params": {"mode": "full"}}
                               )

        assert response.status_code == 200
        response_json = response.json()

        assert 'categories' in response_json
        categories = response_json['categories']

        collection_titles = [gcat['collection_title'] for gcat in categories if gcat['type'] == 'related']
        print(collection_titles)
        assert 'Yu-Gi-Oh! characters' not in collection_titles


@mark.usefixtures("grouped_test_pipelines")
@mark.integration_test
class TestGrouped:
    def test_diversity_parameters(self, test_client):
        # at least for one of the labels results should be different
        for label in ['pinkfloyd', 'spears', 'kyiv', 'ronaldo', 'bohr', 'buildings', 'births', 'deaths']:
            titles = []
            for diversity_parameters in [
                {'label_diversity_ratio': 1.0, 'max_per_type': 1},
                {'label_diversity_ratio': 0.5, 'max_per_type': 2},
                {'label_diversity_ratio': None, 'max_per_type': None},
            ]:
                response = test_client.post("/suggestions_by_category", json={
                    "label": label,
                    "categories": {
                        "related": {
                                       "enable_learning_to_rank": True,
                                       "max_labels_per_related_collection": 10,
                                       "max_recursive_related_collections": 0,
                                       "max_related_collections": 10,
                                   } | diversity_parameters,
                    }
                })

                assert response.status_code == 200
                categories = response.json()['categories']
                collection_names = [c['collection_title'] for c in categories if c['type'] == 'related']
                titles.append(collection_names)

            for el in titles:
                if el != titles[0]:
                    return

        assert False, "Results are the same for all diversity parameters"

    @pytest.mark.parametrize("label", ["zeus", "dog", "dogs", "superman", "[003fda97309fd6aa9d7753dcffa37a] 12345"])
    def test_prod_grouped_by_category(self, test_client, label):
        client = test_client

        request_data = {
            "label": label,
            "params": {
                "user_info": {
                    "user_wallet_addr": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                    "user_ip_addr": "192.168.0.1",
                    "session_id": "d6374908-94c3-420f-b2aa-6dd41989baef",
                    "user_ip_country": "us"
                },
                "mode": "full",
                "metadata": True
            },
            "categories": {
                "related": {
                    "enable_learning_to_rank": True,
                    "max_labels_per_related_collection": 10,
                    "max_per_type": 2,
                    "max_recursive_related_collections": 3,
                    "max_related_collections": 6,
                    "label_diversity_ratio": 0.5
                },
                "wordplay": {
                    "max_suggestions": 10,
                    "min_suggestions": 2
                },
                "alternates": {
                    "max_suggestions": 10,
                    "min_suggestions": 2
                },
                "emojify": {
                    "max_suggestions": 10,
                    "min_suggestions": 2
                },
                "community": {
                    "max_suggestions": 10,
                    "min_suggestions": 2
                },
                "expand": {
                    "max_suggestions": 10,
                    "min_suggestions": 2
                },
                "gowild": {
                    "max_suggestions": 10,
                    "min_suggestions": 2
                },
                "other": {
                    "max_suggestions": 10,
                    "min_suggestions": 6,
                    "min_total_suggestions": 50
                }
            }
        }
        response = client.post("/suggestions_by_category", json=request_data)
        assert response.status_code == 200
        response_json = response.json()

        assert 'categories' in response_json
        categories = response_json['categories']
        # keeping other max_suggestions is more important than min_total_suggestions
        assert (sum([len(gcat['suggestions']) for gcat in categories if gcat['type']=='other']) == request_data['categories']['other'][
            'max_suggestions'] or
                sum([len(gcat['suggestions']) for gcat in categories]) >= request_data['categories']['other'][
            'min_total_suggestions'])

        for category in categories:
            if category['type'] == 'related':
                if category['collection_members_count'] > 10:
                    assert len(category['suggestions']) == 10

        # check min and max suggestions limits in categories
        related_count = 0
        for category in categories:
            print(category['name'])
            if category['type'] == 'related':
                assert len(category['suggestions']) <= request_data['categories'][category['type']][
                    'max_labels_per_related_collection']
                related_count += 1
            else:
                if category['type'] != 'other':
                    assert len(category['suggestions']) >= request_data['categories'][category['type']][
                        'min_suggestions']
                assert len(category['suggestions']) <= request_data['categories'][category['type']]['max_suggestions']

        assert related_count <= request_data['categories']['related']['max_related_collections']

        last_related_flag = False
        actual_type_order = []
        for i, gcat in enumerate(categories):
            assert 'type' in gcat
            assert gcat['type'] in (
                'related', 'wordplay', 'alternates', 'emojify', 'community', 'expand', 'gowild', 'other')
            if gcat['type'] not in actual_type_order:
                actual_type_order.append(gcat['type'])

            assert 'name' in gcat
            if gcat['type'] != 'related':
                assert gcat['name'] in (
                    'Word Play', 'Alternates', '😍 Emojify', 'Community', 'Expand', 'Go Wild', 'Other Names')

            assert all([(s.get('metadata', None) is not None) is True for s in gcat['suggestions']])

            # assert related are after one another
            if gcat['type'] == 'related':
                assert not last_related_flag
                assert {'type', 'name', 'collection_id', 'collection_title', 'collection_members_count', 'suggestions',
                        'related_collections'} \
                       == set(gcat.keys())
                assert gcat['name'] == gcat['collection_title']
                # we could assert that it's greater than len(gcat['suggestions']), but we may produce more suggestions
                # from a single member, so it's not a good idea
                assert gcat['collection_members_count'] > 0
                if i + 1 < len(categories) and categories[i + 1]['type'] != 'related':
                    last_related_flag = True

        # ensure the correct order of types (allow skipping types)
        expected_order = [gcat_type for gcat_type in ['related', 'alternates', 'wordplay', 'emojify',
                                                      'community', 'expand', 'gowild', 'other'] if
                          gcat_type in actual_type_order]
        assert actual_type_order == expected_order  # conf.generation.grouping_categories_order

        # no duplicated suggestions within categories
        related_suggestions = []
        for gcat in categories:
            suggestions = [s['label'] for s in gcat['suggestions']]
            print(gcat['type'], gcat['name'])
            print(suggestions)
            if gcat['type'] == 'related':
                related_suggestions.extend(suggestions)
            else:
                assert len(suggestions) == len(set(suggestions))
        assert len(related_suggestions) == len(set(related_suggestions))

    @pytest.mark.integration_test
    @pytest.mark.parametrize("label", ["zeus", "dog", "dogs", "superman"])
    def test_prod_related_collections_duplicates(self, test_client, label):
        client = test_client

        request_data = {
            "label": label,
            "categories": {
                "related": {
                    "enable_learning_to_rank": True,
                    "max_labels_per_related_collection": 10,
                    "max_per_type": 2,
                    "max_recursive_related_collections": 3,
                    "max_related_collections": 6,
                    "label_diversity_ratio": 0.5
                },
            }
        }
        response = client.post("/suggestions_by_category", json=request_data)
        assert response.status_code == 200
        response_json = response.json()

        assert 'categories' in response_json
        categories = response_json['categories']

        collections_used = []
        for category in categories:
            if category['type'] != 'related':
                continue

            collections_used.append(category['collection_id'])
            collections_used.extend([
                related_collection['collection_id']
                for related_collection in category['related_collections']
            ])

        assert len(collections_used) == len(set(collections_used))

    @pytest.mark.parametrize("label", ["pinkfloyd", "kyiv", "bohr", "dog", "dogs"])
    def test_returned_collection_ids(self, test_client, label):
        response = test_client.post("/suggestions_by_category", json={
            "label": label,
            "categories": {
                "related": {
                    "max_recursive_related_collections": 0,
                    "max_related_collections": 10,
                }
            }
        })

        assert response.status_code == 200
        categories = response.json()['categories']
        for category in categories:
            if category['type'] != 'related':
                continue

            collection_id = category['collection_id']
            # most wikidata ids are no longer than 12 symbols
            # instead our generated ids are 12 symbols long
            assert len(collection_id) >= 12

    def test_fetching_top_collection_members(self, test_client):
        client = test_client
        collection_id = 'JCzsKPv4HQ2N'  # Q15102072

        response = client.post("/fetch_top_collection_members",
                               json={"collection_id": collection_id})

        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json) <= 10

        for name in response_json['suggestions']:
            assert name['metadata']['pipeline_name'] == 'fetch_top_collection_members'
            assert name['metadata']['collection_id'] == collection_id

    def test_test_fetching_top_collection_members_tokenized(self, test_client):
        client = test_client
        collection_id = 'ri2QqxnAqZT7'  # Music artists and bands from England

        label2tokens = {
            "dualipa": ("dua", "lipa"),
            "thebeatles": ("the", "beatles"),
            "davidbowie": ("david", "bowie")
        }

        response = client.post("/fetch_top_collection_members",
                               json={"collection_id": collection_id})

        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json) <= 10

        for item in response_json['suggestions']:
            assert ''.join(item['tokenized_label']) == item['label']
            if item['label'] in label2tokens:
                assert tuple(item['tokenized_label']) == label2tokens[item['label']]


    @pytest.mark.xfail(reason="Enable when we move filtered collections to use a separate field") # TODO
    def test_fetching_top_collection_members_archived(self, test_client):
        client = test_client
        collection_id = 'B1r8GhHWIgAA'  # archived

        response = client.post("/fetch_top_collection_members",
                               json={"collection_id": collection_id})

        assert response.status_code == 410
