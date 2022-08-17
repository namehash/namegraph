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


@mark.parametrize(
    "overrides",
    [
        (["app.query=dogcatdog", "app.suggestions=1000"]),
    ],
)
def test_duplicates_in_suggestions(overrides: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        pipeline = Pipeline(config.pipelines[1], config)
        result = pipeline.apply(config.app.query)

        words = [str(name) for name in result]

        assert len(set(words)) == len(result)


@mark.parametrize(
    "overrides, pipeline_id, expected_strategies",
    [
        (
            ["app.query=firepower", "app.suggestions=1000"],
            0,
            [[
                "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                "LongNameNormalizer", "BigramWordnetTokenizer", "WordnetSynonymsGenerator", "SubnameFilter",
                "ValidNameFilter"
            ]]
        ),
        (
            ["app.query=firepower", "app.suggestions=1000"],
            1,
            [[
                "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                "LongNameNormalizer", "WordNinjaTokenizer", "PermuteGenerator", "SubnameFilter",
                "ValidNameFilter"
            ]]
        )
    ]
)
def test_metadata(overrides: List[str], pipeline_id: int, expected_strategies: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        pipeline = Pipeline(config.pipelines[pipeline_id], config)
        result = pipeline.apply(config.app.query)

        for gn in result:
            assert gn.applied_strategies == expected_strategies


@mark.parametrize(
    "overrides, pipeline_id, expected_strategies",
    [
        (
            ["app.query=dogcatdog", "app.suggestions=1000"],
            1,
            [[
                "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                "LongNameNormalizer", "WordNinjaTokenizer", "PermuteGenerator", "SubnameFilter",
                "ValidNameFilter"
            ]] * 2  # duplicate
        )
    ]
)
def test_metadata_aggregation_same_pipeline(overrides: List[str], pipeline_id: int, expected_strategies: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        pipeline = Pipeline(config.pipelines[pipeline_id], config)
        result = pipeline.apply(config.app.query)

        for gn in result:
            assert gn.applied_strategies == expected_strategies


@mark.parametrize(
    "overrides, pipeline_id, expected_strategies",
    [
        (
            ["app.query=dogcat", "app.suggestions=1000"],
            2,
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
def test_metadata_aggregation_different_pipelines(overrides: List[str], pipeline_id: int, expected_strategies: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        pipeline = Pipeline(config.pipelines[pipeline_id], config)
        result = pipeline.apply(config.app.query)

        for gn in result:
            assert gn.applied_strategies == expected_strategies
