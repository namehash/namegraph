from typing import List

import pytest
from hydra import initialize, compose
from pytest import mark

from generator.app import generate


@mark.parametrize(
    "overrides",
    [
        (["app.query=dog", "app.suggestions=4", "pipelines=test_combining"]),
    ],
)
def test_pipeline_override(overrides: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        cfg = compose(config_name="test_config", overrides=overrides)
        result = generate(cfg, )[0]
        primary = [str(r) for r in result]
        assert set(primary) == {'thedog', 'dogman', '0xdog', 'dogcoin'}
