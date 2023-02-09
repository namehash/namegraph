from typing import List

from pytest import mark

from generator.generated_name import GeneratedName

from utils import assert_applied_strategies_are_equal


@mark.parametrize(
    "strategies, expected_strategies",
    [
        (
            [["1", "2"], ["4", "5"], ["1", "2"]],
            [["1", "2"], ["4", "5"]]
        )
    ]
)
@mark.xfail
def test_applied_strategies_constructor(strategies: List[List[str]], expected_strategies: List[List[str]]):
    name = GeneratedName(tuple(), applied_strategies=strategies)
    assert_applied_strategies_are_equal(name.applied_strategies, expected_strategies)


@mark.parametrize(
    "constructor_strategies, strategies, expected_strategies",
    [
        (
            [["1", "2"], ["3", "15"]],
            [["1", "2"], ["4", "5"], ["1", "2"]],
            [["1", "2"], ["4", "5"], ["3", "15"]]
        )
    ]
)
@mark.xfail
def test_applied_strategies_add_strategies(constructor_strategies: List[List[str]],
                                           strategies: List[List[str]],
                                           expected_strategies: List[List[str]]):

    name = GeneratedName(tuple(), applied_strategies=constructor_strategies)
    name.add_strategies(strategies)
    assert_applied_strategies_are_equal(name.applied_strategies, expected_strategies)


@mark.parametrize(
    "constructor_strategies, point, expected_strategies",
    [
        (
            [["1", "2"], ["3", "15"], ["1", "2"]],
            "16",
            [["1", "2", "16"], ["3", "15", "16"]]
        )
    ]
)
@mark.xfail
def test_applied_strategies_append_strategy_point(constructor_strategies: List[List[str]],
                                                  point: str,
                                                  expected_strategies: List[List[str]]):
    name = GeneratedName(tuple(), applied_strategies=constructor_strategies)
    name.append_strategy_point(point)
    assert_applied_strategies_are_equal(name.applied_strategies, expected_strategies)
