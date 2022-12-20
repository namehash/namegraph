import io

from generator.app import generate
from hydra import compose, initialize_config_module, initialize

import pytest
from pytest import mark
from typing import List

from generator.domains import Domains

from utils import assert_applied_strategies_are_equal


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=firepower", "app.suggestions=1000", "app.internet_domains=tests/data/top_internet_names_long.csv"],
         ["fireability", "fireforce", "firemight"]),
    ],
)
def test_basic_generation(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        result = [str(gn) for gn in result]
        assert len(set(result).intersection(set(expected))) == len(expected)
        assert len(result) == 1000


@pytest.mark.slow
@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=firepower", "pipelines=full",
          "app.suggestions=1000", "app.internet_domains=tests/data/top_internet_names_long.csv"],
         ["firepowercoin"]),
    ],
)
def test_pipeline_override(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        result = [str(gn) for gn in result]
        assert len(set(result).intersection(set(expected))) == len(expected)
        assert len(result) == cfg.app.suggestions


@mark.parametrize(
    "overrides, expected",
    [
        (["app.input=stdin", "app.suggestions=1000", "app.internet_domains=tests/data/top_internet_names_long.csv"],
         ["fireability", "fireforce", "firemight"]),
    ],
)
def test_stdin(overrides: List[str], expected: List[str], monkeypatch) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        monkeypatch.setattr('sys.stdin', io.StringIO('firepower'))
        result = generate(cfg, )[0]
        result = [str(gn) for gn in result]
        assert len(set(result).intersection(set(expected))) == len(expected)
        assert len(result) == 1000


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=pandas", "app.suggestions=1000", "app.internet_domains=tests/data/top_internet_names_long.csv"],
         ["panda"]),
    ],
)
def test_advertised(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        result = [str(gn) for gn in result]
        assert len(set(result).intersection(set(expected))) == len(expected)


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=fires", "app.suggestions=1000", "app.internet_domains=tests/data/top_internet_names_long.csv"],
         ["fire"]),
    ],
)
def test_on_sale(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        result = [str(gn) for gn in result]
        assert len(set(result).intersection(set(expected))) == len(expected)


@mark.parametrize(
    "overrides, expected_strategies",
    [
        (
            ["app.query=dogcat", "app.suggestions=1000", "app.internet_domains=tests/data/top_internet_names_long.csv"],
            [[
                "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                "LongNameNormalizer", "WordNinjaTokenizer", "PermuteGenerator", "SubnameFilter",
                "ValidNameFilter"
              ], [
                "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                "LongNameNormalizer", "BigramWordnetTokenizer", "PermuteGenerator", "SubnameFilter",
                "ValidNameFilter"
            ]]
        )
    ]
)
def test_metadata(overrides: List[str], expected_strategies: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]

        catdog_result = [gn for gn in result if str(gn) == "catdog"]
        assert len(catdog_result) == 1
        assert_applied_strategies_are_equal(catdog_result[0].applied_strategies, expected_strategies)


@mark.parametrize(
    "overrides",
    [
        (["app.query=tubeyou", "app.suggestions=1000", "app.internet_domains=tests/data/top_internet_names_long.csv"])
    ]
)
def test_no_duplicates(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]

        unique_results = set([str(gn) for gn in result])
        assert len(unique_results) == len(result)
