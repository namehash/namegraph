import io

from generator.app import generate
from hydra import compose, initialize_config_module, initialize

import pytest
from pytest import mark
from typing import List


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=firepower", "app.suggestions=1000"], ["fireability", "fireforce", "firemight"]),
    ],
)
def test_basic_generation(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="config", overrides=overrides)
        result = generate(cfg, )[0]
        assert len(set(result).intersection(set(expected))) == len(expected)


@mark.parametrize(
    "overrides, expected",
    [
        (["app.input=stdin", "app.suggestions=1000"], ["fireability", "fireforce", "firemight"]),
    ],
)
def test_stdin(overrides: List[str], expected: List[str], monkeypatch) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="config", overrides=overrides)
        monkeypatch.setattr('sys.stdin', io.StringIO('firepower'))
        result = generate(cfg, )[0]
        assert len(set(result).intersection(set(expected))) == len(expected)
