import os
import sys
from time import time as get_time

import pytest
from fastapi.testclient import TestClient
from hydra import initialize, compose
from ens_normalize import is_ens_normalized, ens_cure

from generator.domains import Domains
from generator.generation.categories_generator import Categories
from generator.collections import CollectionMatcher

from helpers import check_generator_response, generate_example_names


@pytest.fixture(scope="module")
def prod_test_client():
    Domains.remove_self()
    Categories.remove_self()
    CollectionMatcher.remove_self()
    # TODO override 'generation.wikipedia2vec_path=tests/data/wikipedia2vec.pkl'
    os.environ['CONFIG_NAME'] = 'prod_config_new'
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


@pytest.mark.slow
def test_namehash_only_primary(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91].eth",
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
    response = client.post("/", json={"name": "fire", "metadata": False})

    assert response.status_code == 200

    json = response.json()
    str_names = [name["name"] for name in json]
    assert "thefire.eth" in str_names


@pytest.mark.execution_timeout(20)
@pytest.mark.slow
def test_prod_long(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "a" * 40000, "metadata": False})

    assert response.status_code == 200


@pytest.mark.slow
def test_generator_stress(prod_test_client):
    client = prod_test_client
    max_duration = 3
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
        "name": name,
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
#         config = compose(config_name="prod_config")
#         domains = Domains(config)
#
#         names = list(domains.registered)[:100] \
#             + list(domains.advertised)[:100] \
#             + list(domains.secondary_market)[:100] \
#             + list(domains.internet)[:100]
#
#         for name in names:
#             response = prod_test_client.post("/", json={
#                 "name": name,
#                 "sorter": "weighted-sampling"
#             })
#
#             assert response.status_code == 200


@pytest.mark.slow
def test_prod_leet(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={"name": "hacker", "sorter": "round-robin", "metadata": False, "min_suggestions": 1000,
                                 "max_suggestions": 1000})

    assert response.status_code == 200

    json = response.json()
    str_names = [name["name"] for name in json]

    assert "h4ck3r.eth" in str_names


@pytest.mark.slow
def test_prod_flag(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={"name": "firecar", "sorter": "round-robin", "metadata": False, "min_suggestions": 1000,
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
                           json={"name": "😊😊😊", "sorter": "round-robin", "metadata": False, "min_suggestions": 1000,
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
        "name": "firepower",
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
        "name": "firepower",
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
        "name": "firepower",
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
        "name": "firepower",
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


@pytest.mark.integration_test
def test_elasticsearch_template_collections_search(prod_test_client):
    client = prod_test_client
    response = client.post("/find_collections_by_string", json={
        "query": "highest mountains",
        "mode": "instant",
        "max_related_collections": 5,
        "max_total_collections": 5
    })

    assert response.status_code == 200
    titles = [collection['title'] for collection in response.json()['related_collections']]
    assert 'Highest mountains on Earth' in titles


@pytest.mark.integration_test
def test_elasticsearch_featured_collections_search(prod_test_client):
    client = prod_test_client
    response = client.post("/find_collections_by_string", json={
        "query": "highestmountains",
        "mode": "instant",
        "max_related_collections": 5,
        "max_total_collections": 5
    })

    assert response.status_code == 200
    titles = [collection['title'] for collection in response.json()['related_collections']]
    assert 'Highest mountains on Earth' in titles


def test_prod_only_random_or_substr_for_non_ascii_input(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={"name": "😊😊😊", "metadata": True,
                                 "params": {
                                     "mode": "full",
                                     "country": 'pl'
                                 }})

    assert response.status_code == 200

    json = response.json()

    assert all([name['metadata']['pipeline_name'] in ('substring', 'random') for name in json])


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
                               json={"name": input_name, "min_suggestions": 50, "max_suggestions": 50,
                                     "params": {
                                         "mode": "full"
                                     }})

        assert response.status_code == 200
        str_names = [name["name"] for name in response.json()]
        for name in str_names:
            assert is_ens_normalized(name), f'input name: "{input_name}"\tunnormalized suggestion: "{name}"'
