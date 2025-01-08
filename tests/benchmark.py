from hydra import compose, initialize_config_module, initialize

import pytest
from pytest import mark
from typing import List

from namegraph.domains import Domains
from namegraph.xgenerator import Generator


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


@pytest.mark.slow
@mark.parametrize(
    "overrides, expected",
    [
        (['generation.wikipedia2vec_path=tests/data/wikipedia2vec.pkl', "app.query=firepower"], ["firepowercoin"]),
    ],
)
def test_pipeline_override(overrides: List[str], expected: List[str], benchmark) -> None:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config", overrides=overrides)
        generator = Generator(config)
        result = benchmark(generator.generate_names, config.app.query)

        # for n in result['primary']:
        #     print(n.applied_strategies)

        primary = [str(gn) for gn in result]
        assert len(set(primary).intersection(set(expected))) == len(expected)
        assert len(primary) == config.app.suggestions
