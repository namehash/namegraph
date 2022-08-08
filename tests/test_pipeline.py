from hydra import compose, initialize

from pytest import mark
from typing import List

from generator.pipeline import Pipeline


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=firepower"], ["fireability", "fireforce", "firemight"]),
    ],
)
def test_basic_pipeline(overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        pipeline = Pipeline(config.pipelines[0], config)
        result = pipeline.apply(config.app.query)
        result = [str(r) for r in result]
        assert len(set(result).intersection(set(expected))) == len(expected)
        assert config.app.query not in result
