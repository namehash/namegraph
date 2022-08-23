import os
import sys
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
    assert "discharge" in primary


def test_get(test_test_client):
    client = test_test_client
    response = client.get("/?name=firę")

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "discharge" in primary


@mark.parametrize(
    "name, expected_name, expected_strategies",
    [(
        "dogcat",
        "catdog",
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
def test_metadata(test_test_client, name: str, expected_name: str, expected_strategies: List[List[str]]):
    client = test_test_client
    response = client.post("/metadata", json={"name": name})

    assert response.status_code == 200

    json = response.json()
    assert sorted(json.keys()) == sorted(["advertised", "primary", "secondary"])

    primary = json["primary"]
    assert len(primary) > 0
    assert sorted(primary[0].keys()) == sorted(["name", "metadata"])

    catdog_result = [name for name in primary if name["name"] == expected_name]
    assert len(catdog_result) == 1

    metadata = catdog_result[0]["metadata"]
    assert "applied_strategies" in metadata
    assert len(metadata["applied_strategies"]) == 2

    for strategy in metadata["applied_strategies"]:
        assert strategy in expected_strategies


@mark.parametrize(
    "name, min_suggestions, max_suggestions",
    [
        ("tubeyou", 30, 30),  # testing padding using random pipeline
        ("firepower", 50, 100)
    ]
)
def test_min_max_suggestions_parameters(test_test_client, name: str, min_suggestions: int, max_suggestions: int):
    client = test_test_client
    response = client.post("/metadata", json={
        "name": name,
        "min_suggestions": min_suggestions,
        "max_suggestions": max_suggestions
    })

    assert response.status_code == 200

    json = response.json()
    assert "primary" in json

    primary = json["primary"]
    unique_names = set([suggestion["name"] for suggestion in primary])
    assert len(unique_names) == len(primary)

    assert min_suggestions <= len(unique_names)
    assert len(unique_names) <= max_suggestions
