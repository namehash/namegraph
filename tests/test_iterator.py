from typing import List

import pytest
from hydra import initialize, compose
from pytest import mark

from generator.xgenerator import by_one_iterator, by_one_iterator_uniq

from generator.app import generate


def test_iterator1():
    lists = [['a1', 'a2', 'a3'], ['b1'], ['c1', 'c2', 'c3']]
    combined = by_one_iterator(lists)
    assert combined == ['a1', 'b1', 'c1', 'a2', 'c2', 'a3', 'c3']


def test_iterator_uniq():
    lists = [['a1', 'a2', 'a3'], ['b1'], ['a1', 'c1', 'c2', 'c3']]
    combined = by_one_iterator_uniq(lists)
    assert list(combined) == ['a1', 'b1', 'c1', 'a2', 'c2', 'a3', 'c3']


@mark.parametrize(
    "overrides",
    [
        (["app.query=dog", "pipelines=test_combining"]),
    ],
)
def test_pipeline_override(overrides: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        assert result['primary'] == ['thedog', 'dogman', '0xdog', 'dogcoin']
