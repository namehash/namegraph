from hydra import compose, initialize

from pytest import mark, fixture
from typing import List

from namegraph.preprocessor import Preprocessor
from namegraph.pipeline import Pipeline
from namegraph.input_name import InputName, Interpretation

from utils import assert_applied_strategies_are_equal


@fixture(scope="module")
def preprocessor_test_config():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        preprocessor = Preprocessor(config)
        return preprocessor


def get_name_and_interpretation(preprocessor_test_config, name):
    input_name = InputName(name, {})
    preprocessor_test_config.normalize(input_name)
    preprocessor_test_config.classify(input_name)
    interpretation = input_name.interpretations[('ngram', 'en')][0]
    return input_name, interpretation


@mark.parametrize(
    "overrides, expected",
    [
        (["app.query=powerfire"], ["abilityfire", "forcefire", "mightfire"]),
    ],
)
def test_basic_pipeline(preprocessor_test_config, overrides: List[str], expected: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        pipeline = Pipeline(config.pipelines[0], config)
        input_name, interpretation = get_name_and_interpretation(preprocessor_test_config, config.app.query)
        result = pipeline.apply(input_name, interpretation)
        result = [str(r) for r in result]
        assert len(set(result).intersection(set(expected))) == len(expected)
        assert config.app.query not in result


@mark.parametrize(
    "overrides",
    [
        (["app.query=dogcatdog", "app.suggestions=1000"]),
    ],
)
@mark.skip(reason='no deduplication in pipelines now')
def test_duplicates_in_suggestions(preprocessor_test_config, overrides: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        pipeline = Pipeline(config.pipelines[1], config)

        input_name, interpretation = get_name_and_interpretation(preprocessor_test_config, config.app.query)

        result = pipeline.apply(input_name, interpretation)

        words = [str(name) for name in result]

        assert len(set(words)) == len(result)


@mark.parametrize(
    "overrides, pipeline_id, expected_strategies",
    [
        (
                ["app.query=powerfire", "app.suggestions=1000"],
                0,
                [[
                    "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                    "LongNameNormalizer", "BigramWordnetTokenizer", "WordnetSynonymsGenerator", "SubnameFilter",
                    "ValidNameFilter"
                ]]
        ),
        (
                ["app.query=powerfire", "app.suggestions=1000"],
                1,
                [[
                    "StripEthNormalizer", "UnicodeNormalizer", "NamehashNormalizer", "ReplaceInvalidNormalizer",
                    "LongNameNormalizer", "WordNinjaTokenizer", "PermuteGenerator", "SubnameFilter",
                    "ValidNameFilter"
                ]]
        )
    ]
)
@mark.xfail
def test_metadata(preprocessor_test_config, overrides: List[str], pipeline_id: int,
                  expected_strategies: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        pipeline = Pipeline(config.pipelines[pipeline_id], config)

        input_name, interpretation = get_name_and_interpretation(preprocessor_test_config, config.app.query)

        result = pipeline.apply(input_name, interpretation)

        # TODO fix
        for gn in result:
            assert_applied_strategies_are_equal(gn.applied_strategies, expected_strategies)


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
                ]]
        )
    ]
)
@mark.xfail
def test_metadata_aggregation_same_strategy(preprocessor_test_config, overrides: List[str], pipeline_id: int,
                                            expected_strategies: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        pipeline = Pipeline(config.pipelines[pipeline_id], config)
        input_name, interpretation = get_name_and_interpretation(preprocessor_test_config, config.app.query)
        result = pipeline.apply(input_name, interpretation)

        for gn in result:
            assert_applied_strategies_are_equal(gn.applied_strategies, expected_strategies)


@mark.parametrize(
    "overrides, pipeline_id, expected_strategies",
    [
        (
                ["app.query=dogcat", "app.suggestions=1000"],
                1,
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
@mark.xfail
def test_metadata_aggregation_different_strategies(preprocessor_test_config, overrides: List[str], pipeline_id: int,
                                                   expected_strategies: List[str]) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        pipeline = Pipeline(config.pipelines[pipeline_id], config)
        input_name, interpretation = get_name_and_interpretation(preprocessor_test_config, config.app.query)
        result = pipeline.apply(input_name, interpretation)

        for gn in result:
            assert_applied_strategies_are_equal(gn.applied_strategies, expected_strategies)


def test_removing_input_from_output(preprocessor_test_config) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pipeline = Pipeline(config.pipelines[0], config)

        input_name, interpretation = get_name_and_interpretation(preprocessor_test_config, 'vitalik.eth')
        result = pipeline.apply(input_name, interpretation)
        result = [str(r) for r in result]
        assert 'vitalik' not in result
