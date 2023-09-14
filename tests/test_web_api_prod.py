import os
import sys
from time import time as get_time

import pytest
from fastapi.testclient import TestClient
from hydra import initialize, compose
from ens_normalize import is_ens_normalized, ens_cure

from generator.domains import Domains
from generator.generation.categories_generator import Categories
from generator.xcollections.api_matcher import CollectionMatcherForAPI
from generator.xcollections.generator_matcher import CollectionMatcherForGenerator

from helpers import check_generator_response, generate_example_names


@pytest.fixture(scope="module")
def prod_test_client():
    Domains.remove_self()
    Categories.remove_self()
    CollectionMatcherForAPI.remove_self()
    CollectionMatcherForGenerator.remove_self()
    # TODO override 'generation.wikipedia2vec_path=tests/data/wikipedia2vec.pkl'
    os.environ['CONFIG_NAME'] = 'prod_config_new'
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.post("/", json={"label": "aaa"})
    return client


# skipped because dots are not allowed
@pytest.mark.skip
def test_namehash(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"label": "[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91].eth",
                                      "metadata": True})

    assert response.status_code == 200

    json = response.json()
    for name in json:
        applied_strategies = name['metadata']['applied_strategies']
        assert any([
            generator in strategy
            for strategy in applied_strategies
            for generator in ['RandomAvailableNameGenerator']
        ])


# skipped because dots are not allowed
@pytest.mark.skip
def test_namehash_only_primary(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"label": "[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91].eth",
                                      "metadata": True, "min_primary_fraction": 1.0})

    assert response.status_code == 200

    json = response.json()
    for name in json:
        applied_strategies = name['metadata']['applied_strategies']
        assert any([
            generator in strategy
            for strategy in applied_strategies
            for generator in ['RandomAvailableNameGenerator']
        ])


@pytest.mark.slow
def test_prod(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"label": "fire", "metadata": False})

    assert response.status_code == 200

    json = response.json()
    str_names = [name["name"] for name in json]
    assert "thefire.eth" in str_names


@pytest.mark.execution_timeout(20)
@pytest.mark.slow
def test_prod_long(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"label": "a" * 40000, "metadata": False})

    assert response.status_code == 200


@pytest.mark.slow
def test_generator_stress(prod_test_client):
    client = prod_test_client
    max_duration = 3
    for nname in generate_example_names(400):
        # use left side of dot-split
        name = nname.split('.')[0]
        start = get_time()
        response = client.post('/', json={"label": name, "metadata": False})
        duration = get_time() - start
        assert response.status_code == 200, f'{name} failed with {response.status_code}'
        assert duration < max_duration, f'Time exceeded on {name}'


def test_metadata(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"label": "dogcat"})

    assert response.status_code == 200

    json = response.json()
    assert len(json) > 0
    print(json)
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
        "label": name,
        "min_suggestions": min_suggestions,
        "max_suggestions": max_suggestions
    })

    assert response.status_code == 200

    json = response.json()
    unique_names = set([suggestion["name"] for suggestion in json])
    assert len(unique_names) == len(json)

    assert min_suggestions <= len(unique_names)
    assert len(unique_names) <= max_suggestions


@pytest.mark.parametrize(
    "name, suggestions, min_primary_fraction, response_code",
    [
        ("firepower", 150, 0.0, 200),
        ("fireworks", 100, 1.0, 200),
        ("firedrinks", 120, 0.1, 200),
        ("firepower", 150, -0.1, 422),
        ("fireworks", 150, 1.1, 422)
    ]
)
def test_min_primary_fraction_parameters(prod_test_client, name: str, suggestions: int,
                                         min_primary_fraction: float, response_code: int):
    client = prod_test_client
    response = client.post("/", json={
        "label": name,
        "min_suggestions": suggestions,
        "max_suggestions": suggestions,
        "min_primary_fraction": min_primary_fraction
    })

    assert response.status_code == response_code

    if response_code == 200:
        json = response.json()
        unique_names = set([suggestion["name"] for suggestion in json])
        assert len(unique_names) == suggestions


# @pytest.mark.slow
# def test_weighted_sampling_sorter_stress(prod_test_client):
#     with initialize(version_base=None, config_path="../conf/"):
#         config = compose(config_name="prod_config_new")
#         domains = Domains(config)
#
#         names = list(domains.registered)[:100] \
#             + list(domains.advertised)[:100] \
#             + list(domains.secondary_market)[:100] \
#             + list(domains.internet)[:100]
#
#         for name in names:
#             response = prod_test_client.post("/", json={
#                 "label": name,
#                 "sorter": "weighted-sampling"
#             })
#
#             assert response.status_code == 200


@pytest.mark.slow
def test_prod_leet(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={"label": "hacker", "sorter": "round-robin", "metadata": False, "min_suggestions": 1000,
                                 "max_suggestions": 1000})

    assert response.status_code == 200

    json = response.json()
    str_names = [name["name"] for name in json]

    assert "h4ck3r.eth" in str_names


@pytest.mark.slow
def test_prod_flag(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={"label": "firecar", "sorter": "round-robin", "metadata": False, "min_suggestions": 1000,
                                 "max_suggestions": 1000, "params": {
                                   "country": 'pl'
                               }})

    assert response.status_code == 200

    json = response.json()
    str_names = [name["name"] for name in json]

    assert "firecar🇵🇱.eth" in str_names
    assert "🇵🇱firecar.eth" in str_names
    assert "_firecar.eth" in str_names
    assert "$firecar.eth" in str_names
    assert "fcar.eth" in str_names
    assert "firec.eth" in str_names
    assert "fire-car.eth" in str_names
    # assert "🅵🅸🆁🅴🅲🅰🆁.eth" in str_names
    assert "fir3c4r.eth" in str_names


@pytest.mark.slow
def test_prod_short_suggestions(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={"label": "😊😊😊", "sorter": "round-robin", "metadata": False, "min_suggestions": 1000,
                                 "max_suggestions": 1000, "params": {
                                   "country": 'pl'
                               }})

    assert response.status_code == 200

    json = response.json()
    str_names = [name["name"] for name in json]

    assert all([len(name) >= 3 for name in str_names])


def test_instant_search(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={
        "label": "firepower",
        "params": {
            "mode": 'instant',
        },
    })
    assert response.status_code == 200
    json = response.json()
    assert len(json) > 0
    assert not any([
        'W2VGenerator' in strategy
        for name in json
        for strategy in name['metadata']['applied_strategies']
    ])


def test_instant_search_temp(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={
        "label": "firepower",
        "params": {
            "mode": "instant",
        },
    })
    assert response.status_code == 200
    json = response.json()
    assert len(json) > 0
    assert not any([
        'W2VGenerator' in strategy
        for name in json
        for strategy in name['metadata']['applied_strategies']
    ])


def test_not_instant_search(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={
        "label": "firepower",
        "params": {
            "mode": 'full',
        },
    })
    assert response.status_code == 200
    json = response.json()
    assert len(json) > 0
    assert any([
        'W2VGenerator' in strategy
        for name in json
        for strategy in name['metadata']['applied_strategies']
    ])


def test_not_instant_search_temp(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={
        "label": "firepower",
        "params": {
            "mode": "full",
        },
    })
    assert response.status_code == 200
    json = response.json()
    assert len(json) > 0
    assert any([
        'W2VGenerator' in strategy
        for name in json
        for strategy in name['metadata']['applied_strategies']
    ])


def test_prod_only_random_or_substr_for_non_ascii_input(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={"label": "😊😊😊", "metadata": True,
                                 "params": {
                                     "mode": "full",
                                     "country": 'pl'
                                 }})

    assert response.status_code == 200

    json = response.json()

    assert all([name['metadata']['pipeline_name'] in ('substring', 'random') for name in json])


@pytest.mark.parametrize(
    "input_label, joined_label",
    [
        ('marvel sky', 'marvelsky'),
        ('crab rave', 'crabrave'),
        ('i love bilbao', 'ilovebilbao'),
        (' a  sequence of   words  ', 'asequenceofwords')
    ]
)
def test_no_joined_input_as_suggestion(prod_test_client, input_label: str, joined_label: str):
    client = prod_test_client
    response = client.post("/", json={"label": input_label, "metadata": True, "params": {"mode": "full"}})

    assert response.status_code == 200
    assert joined_label + '.eth' not in [name["name"] for name in response.json()]


@pytest.mark.slow
def test_prod_normalization_with_ens_normalize(prod_test_client):
    client = prod_test_client
    input_names = ['fire', 'funny', 'funnyshit', 'funnyshitass', 'funnyshitshit', 'lightwalker', 'josiahadams',
                   'kwrobel', 'krzysztofwrobel', 'pikachu', 'mickey', 'adoreyoureyes', 'face', 'theman', 'goog',
                   'billycorgan', '[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91]', 'a' * 101,
                   'dogcat', 'firepower', 'tubeyou', 'fireworks', 'hacker', 'firecar', '😊😊😊', 'anarchy',
                   'prayforukraine', 'krakowdragon', 'fiftysix', 'あかまい', '💛', 'asd', 'bartek', 'hongkong',
                   'hongkonger', 'tyler', 'asdfasdfasdf3453212345', 'nineinchnails', 'krakow', 'joebiden',
                   'europeanunion', 'rogerfederer', 'suzuki', 'pirates', 'doge', 'ethcorner', 'google', 'apple', '001',
                   'stop-doing-fake-bids-its-honestly-lame-my-guy', 'kfcsogood', 'wallet', 'الأبيض', 'porno', 'sex',
                   'slutwife', 'god', 'imexpensive', 'htaccess', 'nike', '€80000', 'starbucks', 'ukraine', '٠٠٩',
                   'sony', 'kevin', 'discord', 'monaco', 'market', 'sportsbet', 'volodymyrzelensky', 'coffee', 'gold',
                   'hodl', 'yeezy', 'brantly', 'jeezy', 'vitalik', 'exampleregistration', 'pyme', 'avalanche', 'messy',
                   'messi', 'kingmessi', 'abc', 'testing', 'superman', 'facebook', 'test', 'namehash', 'testb',
                   'happypeople', 'muscle', 'billybob', 'quo', 'circleci', 'bitcoinmine', 'poweroutage',
                   'shootingarrowatthesky']
    for input_name in input_names:
        response = client.post("/",
                               json={"label": input_name, "min_suggestions": 50, "max_suggestions": 50,
                                     "params": {
                                         "mode": "full"
                                     }})

        assert response.status_code == 200
        str_names = [name["name"] for name in response.json()]
        for name in str_names:
            assert is_ens_normalized(name), f'input name: "{input_name}"\tunnormalized suggestion: "{name}"'


@pytest.mark.parametrize(
    "ip_addr, response_code",
    [
        ("215.13.137.21", 200),
        ("2001:db8::ff00:42:8329", 200),
        ("256.0.0.1", 422),  # not an ipv4 address
    ]
)
def test_prod_user_info_ip(prod_test_client, ip_addr, response_code):
    client = prod_test_client
    response = client.post("/",
                           json={"label": "whatever", "min_suggestions": 50, "max_suggestions": 50,
                                 "params": {
                                     "mode": "full",
                                     "user_info": {
                                         "user_wallet_addr": 'abc123',
                                         "user_ip_addr": ip_addr,
                                         "session_id": 'h98732hr59hwh'
                                     }
                                 }})
    assert response.status_code == response_code
    response_json = response.json()
    print(response_json)


class TestGroupedSuggestions:

    @staticmethod
    def strategy_not_used(gcat_dict: dict, strategy: str) -> bool:
        return all([strategy not in s['metadata']['applied_strategies'][0] for s in gcat_dict['suggestions']
                    if 'metadata' in s and s['metadata'] and s['metadata']['applied_strategies']])

    @pytest.mark.integration_test
    @pytest.mark.parametrize(
        "name, metadata, n_suggestions, response_code",
        [
            ("jamesbond", True, 50, 200),
            ("soundgarden", True, 50, 200),
            ("aligator", True, 50, 200),
            ("burdenofdreams", False, 50, 200)
        ]
    )
    def test_prod_order(self, prod_test_client, name, metadata, n_suggestions, response_code):
        client = prod_test_client

        response = client.post("/grouped_by_category",
                               json={"label": name, "min_suggestions": n_suggestions, "max_suggestions": n_suggestions,
                                     "metadata": metadata, "params": {"mode": "instant"}})

        assert response.status_code == response_code
        response_json = response.json()
        print(response_json)

        assert 'categories' in response_json
        categories = response_json['categories']
        assert sum([len(gcat['suggestions']) for gcat in categories]) == n_suggestions

        last_related_flag = False
        actual_type_order = []

        for i, gcat in enumerate(categories):
            assert 'type' in gcat
            assert gcat['type'] in ('related', 'wordplay', 'alternates', 'emojify', 'community', 'expand', 'gowild', 'other')
            if gcat['type'] not in actual_type_order:
                actual_type_order.append(gcat['type'])

            assert 'name' in gcat
            if gcat['type'] != 'related':
                assert gcat['name'] in ('Word Play', 'Alternates', '😍 Emojify', 'Community', 'Expand', 'Go Wild', 'Other Names')

            assert all([(s.get('metadata', None) is not None) is metadata for s in gcat['suggestions']])

            # assert related are after one another
            if gcat['type'] == 'related':
                assert not last_related_flag
                assert {'type', 'name', 'collection_id', 'collection_title', 'collection_members_count', 'suggestions', 'related_collections'} \
                       == set(gcat.keys())
                assert gcat['name'] == gcat['collection_title']
                # we could assert that it's greater than len(gcat['suggestions']), but we may produce more suggestions
                # from a single member, so it's not a good idea
                assert gcat['collection_members_count'] > 0
                if i + 1 < len(categories) and categories[i + 1]['type'] != 'related':
                    last_related_flag = True

        # ensure the correct order of types (allow skipping types)
        expected_order = [gcat_type for gcat_type in ['related', 'alternates', 'wordplay', 'emojify',
                                                      'community', 'expand', 'gowild', 'other'] if gcat_type in actual_type_order]
        assert actual_type_order == expected_order  # conf.generation.grouping_categories_order


    @pytest.mark.integration_test
    @pytest.mark.parametrize(
        "name, metadata, n_suggestions, response_code",
        [
            ("vesperlynd", True, 50, 200),
            ("aliceinchains", True, 50, 200),
            ("saltwatercrocodile", True, 50, 200),
            ("sleepwalker", False, 50, 200)
        ]
    )
    def test_prod_disabled_strategies(self, prod_test_client, name, metadata, n_suggestions, response_code):
        client = prod_test_client

        response = client.post("/grouped_by_category",
                               json={"label": name, "min_suggestions": n_suggestions, "max_suggestions": n_suggestions,
                                     "metadata": metadata, "params": {"mode": "instant"}})

        assert response.status_code == response_code
        response_json = response.json()
        print(response_json)

        assert 'categories' in response_json
        categories = response_json['categories']
        assert sum([len(gcat['suggestions']) for gcat in categories]) == n_suggestions

        for i, gcat in enumerate(categories):
            assert all([(s.get('metadata', None) is not None) is metadata for s in gcat['suggestions']])
            assert self.strategy_not_used(gcat, 'EasterEggGenerator')
            assert self.strategy_not_used(gcat, 'CategoryGenerator')


    @pytest.mark.parametrize("label", ["zeus", "dog", "dogs", "superman"])
    def test_prod_grouped_by_category(self, prod_test_client, label):
        client = prod_test_client

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
                    "max_names_per_related_collection": 10,
                    "max_per_type": 2,
                    "max_recursive_related_collections": 3,
                    "max_related_collections": 6,
                    "name_diversity_ratio": 0.5
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
        assert sum([len(gcat['suggestions']) for gcat in categories]) >= request_data['categories']['other'][
            'min_total_suggestions']

        # check min and max suggestions limits in categories
        related_count = 0
        for category in categories:
            print(category['name'])
            if category['type'] == 'related':
                assert len(category['suggestions']) <= request_data['categories'][category['type']][
                    'max_names_per_related_collection']
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
            suggestions = [s['name'] for s in gcat['suggestions']]
            print(gcat['type'], gcat['name'])
            print(suggestions)
            if gcat['type'] == 'related':
                related_suggestions.extend(suggestions)
            else:
                assert len(suggestions) == len(set(suggestions))
        assert len(related_suggestions) == len(set(related_suggestions))


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "collection_id, max_sample_size",
    [
        ("JCzsKPv4HQ2N", 5),  # Q15102072
        ("JCzsKPv4HQ2N", 20),  # Q15102072
        ("xEvCGnUB3syi", 4),  # Q8377580 - collection has only 5 members, only unique names should be returned
        ("xEvCGnUB3syi", 10),  # Q8377580 - collection has only 5 members, all names should be returned
    ]
)
def test_collection_members_sampling(prod_test_client, collection_id, max_sample_size):
    client = prod_test_client

    response = client.post("/sample_collection_members",
                           json={"collection_id": collection_id, "max_sample_size": max_sample_size, "seed": 42})

    assert response.status_code == 200
    response_json = response.json()

    assert len(response_json) <= max_sample_size
    for name in response_json:
        assert name['metadata']['pipeline_name'] == 'sample_collection_members'
        assert name['metadata']['collection_id'] == collection_id

    # uniqueness
    names = [name['name'] for name in response_json]
    assert len(names) == len(set(names))


@pytest.mark.integration_test
def test_fetching_top_collection_members(prod_test_client):
    client = prod_test_client
    collection_id = 'JCzsKPv4HQ2N'  # Q15102072

    response = client.post("/fetch_top_collection_members",
                           json={"collection_id": collection_id})

    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) <= 10

    for name in response_json['suggestions']:
        assert name['metadata']['pipeline_name'] == 'fetch_top_collection_members'
        assert name['metadata']['collection_id'] == collection_id


class TestTokenScramble:
    @pytest.mark.integration_test
    def test_left_right_shuffle(self, prod_test_client):
        client = prod_test_client
        collection_id = 'dzifE0uLLXb0'

        response = client.post("/scramble_collection_tokens",
                               json={
                                   "collection_id": collection_id,
                                   "method": 'left-right-shuffle',
                                   "n_top_members": 25
                               })

        assert response.status_code == 200
        response_json = response.json()
        print(response_json)

        assert len(response_json) <= 25  # always <= n_top_members (if n_suggestions=None)

        for name in response_json:
            assert name['metadata']['pipeline_name'] == 'scramble_collection_tokens'
            assert name['metadata']['collection_id'] == collection_id

        # uniqueness
        names = [name['name'] for name in response_json]
        assert len(names) == len(set(names))


        @pytest.mark.integration_test
        def test_left_right_shuffle_with_unigrams_interesting_names(self, prod_test_client):
            client = prod_test_client
            collection_id = '3OB_f2vmyuyp'  # tropical fruit

            response = client.post("/scramble_collection_tokens",
                                   json={
                                       "collection_id": collection_id,
                                       "method": 'left-right-shuffle-with-unigrams',
                                       "n_top_members": 5  # avocado, pine-apple, jack-fruit, coconut, egg-plant
                                   })

            assert response.status_code == 200
            response_json = response.json()
            print(response_json)

            # 3 bigrams + 2 unigrams (can produce 3 results if original name remains at the end)
            assert len(response_json) in (3, 4)

            names = [name['name'] for name in response_json]
            assert len(names) == len(set(names))

            for s in names:
                if s.startswith('egg'):
                    assert s[3:] in ('avocado', 'apple', 'fruit', 'coconut')
                elif s.endswith('apple'):
                    assert s[4:] in ('avocado', 'jack', 'coconut', 'egg')


        @pytest.mark.integration_test
        def test_full_shuffle(self, prod_test_client):
            client = prod_test_client
            collection_id = '3OB_f2vmyuyp'  # tropical fruit

            response = client.post("/scramble_collection_tokens",
                                   json={
                                       "collection_id": collection_id,
                                       "method": 'left-right-shuffle-with-unigrams',
                                       "n_top_members": 5  # avocado, pine-apple, jack-fruit, coconut, egg-plant
                                   })

            assert response.status_code == 200
            response_json = response.json()
            print(response_json)

            assert len(response_json) == 4  # 8 tokens -> 4 bigrams (if n_suggestions=None)

            names = [name['name'] for name in response_json]
            assert len(names) == len(set(names))

        @pytest.mark.integration_test
        def test_full_shuffle_repeat_tokens(self, prod_test_client):
            client = prod_test_client
            collection_id = '3OB_f2vmyuyp'  # tropical fruit

            response = client.post("/scramble_collection_tokens",
                                   json={
                                       "collection_id": collection_id,
                                       "method": 'full-shuffle',
                                       "n_top_members": 5,  # avocado, pine-apple, jack-fruit, coconut, egg-plant,
                                       'n_suggestions': 100
                                   })

            assert response.status_code == 200
            response_json = response.json()
            print(response_json)

            assert len(response_json) == 100
