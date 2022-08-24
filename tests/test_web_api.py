import os
import sys
import itertools
from typing import List

import pytest
from pytest import mark
from fastapi.testclient import TestClient

from generator.domains import Domains


@pytest.fixture(scope="module")
def test_test_client():
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
    client.get("/?name=aaa.eth")
    return client


def test_read_main(test_test_client):
    client = test_test_client
    response = client.post("/", json={"name": "fire"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "discharge.eth" in primary


def test_get(test_test_client):
    client = test_test_client
    response = client.get("/?name=firę")

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "discharge.eth" in primary


@mark.parametrize(
    "name",
    [
        "dogcat"
    ]
)
def test_metadata_scheme(test_test_client, name: str):
    client = test_test_client
    response = client.post("/metadata", json={"name": name})

    assert response.status_code == 200

    json = response.json()
    assert sorted(json.keys()) == sorted(["advertised", "primary", "secondary"])

    for generated_name in itertools.chain(json["advertised"], json["secondary"], json["primary"]):
        assert sorted(generated_name.keys()) == sorted(["name", "nameguard_rating", "metadata"])
        assert sorted(generated_name["metadata"].keys()) == sorted(["applied_strategies"])


@mark.parametrize(
    "name, expected_strategies",
    [(
        "dogcat",
        [
            [
                "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                "LongNameNormalizer", "WordNinjaTokenizer", "PermuteGenerator", "SubnameFilter",
                "ValidNameFilter"
            ],
            [
                "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                "LongNameNormalizer", "BigramWordnetTokenizer", "PermuteGenerator", "SubnameFilter",
                "ValidNameFilter"
            ]
        ]
    )]
)
def test_metadata_applied_strategies(test_test_client, name: str, expected_strategies: List[List[str]]):
    client = test_test_client
    response = client.post("/metadata", json={"name": name})

    assert response.status_code == 200

    json = response.json()
    assert sorted(json.keys()) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert len(primary) > 0

    catdog_result = [name for name in primary if name["name"] == "catdog.eth"]

    assert len(catdog_result) == 1

    metadata = catdog_result[0]["metadata"]
    assert "applied_strategies" in metadata
    assert len(metadata["applied_strategies"]) == 2

    for strategy in metadata["applied_strategies"]:
        assert strategy in expected_strategies


@mark.parametrize(
    "name",
    [
        "firepower",
        "fire",
        "dogcat",
        "anarchy"
    ]
)
def test_count_sorter(test_test_client, name: str):
    client = test_test_client
    response = client.post("/metadata", json={"name": name, "sorter": "count"})

    assert response.status_code == 200

    json = response.json()
    assert "primary" in json

    primary = json["primary"]
    assert len(primary) > 0

    scores = [len(gn["metadata"]["applied_strategies"]) for gn in primary]
    assert all(first >= second for first, second in zip(scores, scores[1:]))


@mark.parametrize(
    "name",
    [
        "firepower",
        "fire",
        "dogcat",
        "anarchy"
    ]
)
def test_length_sorter(test_test_client, name: str):
    client = test_test_client
    response = client.post("/metadata", json={"name": name, "sorter": "length"})

    assert response.status_code == 200

    json = response.json()
    assert "primary" in json

    primary = json["primary"]
    assert len(primary) > 0

    lengths = [len(gn["name"]) for gn in primary]
    print(lengths, [gn["name"] for gn in primary])
    assert all([first <= second for first, second in zip(lengths, lengths[1:])])
