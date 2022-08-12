import io

from generator.app import generate
from hydra import compose, initialize_config_module, initialize

import pytest
from pytest import mark
from typing import List

from generator.domains import Domains


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=firepower", "app.suggestions=1000"], ["fireability", "fireforce", "firemight"]),
    ],
)
def test_basic_generation(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        primary=[str(gn) for gn in result['primary']]
        assert len(set(primary).intersection(set(expected))) == len(expected)
        assert len(primary) >= 100

        assert 'primary' in result
        assert 'secondary' in result
        assert 'advertised' in result

        assert 'wikipedia' in primary  # from random


@pytest.mark.slow
@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=firepower", "pipelines=full"], ["firepowercoin"]),
    ],
)
def test_pipeline_override(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        primary = [str(gn) for gn in result['primary']]
        assert len(set(primary).intersection(set(expected))) == len(expected)
        assert len(primary) == cfg.app.suggestions


@mark.parametrize(
    "overrides, expected",
    [
        (["app.input=stdin", "app.suggestions=1000"], ["fireability", "fireforce", "firemight"]),
    ],
)
def test_stdin(overrides: List[str], expected: List[str], monkeypatch) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        monkeypatch.setattr('sys.stdin', io.StringIO('firepower'))
        result = generate(cfg, )[0]
        primary = [str(gn) for gn in result['primary']]
        assert len(set(primary).intersection(set(expected))) == len(expected)
        assert len(primary) >= 100


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=pandas", "app.suggestions=1000"], ["panda"]),
    ],
)
def test_advertised(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        advertised = [str(gn) for gn in result['advertised']]
        assert len(set(advertised).intersection(set(expected))) == len(expected)


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=fires", "app.suggestions=1000"], ["fire"]),
    ],
)
def test_secondary(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        secondary = [str(gn) for gn in result['secondary']]
        assert len(set(secondary).intersection(set(expected))) == len(expected)
