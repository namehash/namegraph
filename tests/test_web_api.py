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


# no aggregation above the pipelines
@mark.xfail(raises=AssertionError)
def test_metadata(test_test_client):
    client = test_test_client
    response = client.post("/metadata", json={"name": "dogcat"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(json.keys()) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert len(primary) > 0
    assert sorted(primary[0].keys()) == sorted(["name", "metadata"])

    catdog_result = [name for name in primary if name["name"] == "catdog"]
    assert len(catdog_result) == 1

    metadata = catdog_result[0]["metadata"]
    # FIXME how can I use parametrized test and pass fixture to it? according to
    # FIXME https://github.com/pytest-dev/pytest/issues/6374 we can do that by
    # FIXME parametrizing fixtures, but that'll be ugly
    assert "applied_strategies" in metadata and metadata["applied_strategies"] == [
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
