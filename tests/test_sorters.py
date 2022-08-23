from typing import List

import pytest
from pytest import mark
from hydra import initialize, compose

from generator.generated_name import GeneratedName
from generator.sorting import CountSorter, RoundRobinSorter

from utils import assert_applied_strategies_are_equal

@mark.parametrize(
    "input, expected_strings",
    [(
        [
            [GeneratedName(('a')), GeneratedName(('aa'))],
            [GeneratedName(('b'))],
            [GeneratedName(('c')), GeneratedName(('c', 'c')), GeneratedName(('c', 'cc')), GeneratedName(('cccc'))]
        ],
        ['a', 'b', 'c', 'aa', 'cc', 'ccc', 'cccc']
    )]
)
def test_round_robin_sorter(input: List[List[GeneratedName]], expected_strings: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        sorter = RoundRobinSorter(config)

        sorted_strings = [str(gn) for gn in sorter.sort(input)]
        assert sorted_strings == expected_strings


@mark.parametrize(
    "input, expected_strings",
    [(
        [
            [GeneratedName(('a'), applied_strategies=[[str(i)] for i in range(15)]),
                GeneratedName(('aa'), applied_strategies=[[str(i)] for i in range(10)])],
            [GeneratedName(('b'), applied_strategies=[[str(i)] for i in range(2)])],
            [GeneratedName(('c'), applied_strategies=[[str(i)] for i in range(4)]),
                GeneratedName(('c', 'c'), applied_strategies=[[str(i)] for i in range(7)]),
                GeneratedName(('cccc'), applied_strategies=[[str(i)] for i in range(5)])]
        ],
        ['a', 'aa', 'cc', 'cccc', 'c', 'b']
    )]
)
def test_count_sorter(input: List[List[GeneratedName]], expected_strings: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        sorter = CountSorter(config)

        print(input[0][0].applied_strategies)

        sorted_strings = [str(gn) for gn in sorter.sort(input)]
        assert sorted_strings == expected_strings


@mark.parametrize(
    "input, expected",
    [(
        [
            [GeneratedName(('a'), applied_strategies=[['1', '2'], ['1', '3']])],
            [GeneratedName(('a'), applied_strategies=[['1', '2', '3']]),
                GeneratedName(('b'), applied_strategies=[['2']])],
            [GeneratedName(('b'), applied_strategies=[['2', '3']])],
            [GeneratedName(('b'), applied_strategies=[['2']])]
        ],
        [
            GeneratedName(('a'), applied_strategies=[['1', '2'], ['1', '3'], ['1', '2', '3']]),
            GeneratedName(('b'), applied_strategies=[['2'], ['2', '3']])
        ]
    )]
)
def test_round_robin_sorter_aggregation(input: List[List[GeneratedName]], expected: List[GeneratedName]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        sorter = RoundRobinSorter(config)

        sorted_names = sorter.sort(input)

        assert len(sorted_names) == len(expected)
        for name, expected in zip(sorted_names, expected):
            assert str(name) == str(expected)
            assert_applied_strategies_are_equal(name.applied_strategies, expected.applied_strategies)


@mark.parametrize(
    "input, expected",
    [(
        [
            [GeneratedName(('a'), applied_strategies=[['1', '2'], ['1', '3']])],
            [GeneratedName(('a'), applied_strategies=[['1', '2', '3']]),
                GeneratedName(('b'), applied_strategies=[['2']])],
            [GeneratedName(('b'), applied_strategies=[['2', '3']])],
            [GeneratedName(('b'), applied_strategies=[['2']])],
            [GeneratedName(('b'), applied_strategies=[['1', '4'], ['5', '6']])]
        ],
        [
            GeneratedName(('b'), applied_strategies=[['2'], ['2', '3'], ['1', '4'], ['5', '6']]),
            GeneratedName(('a'), applied_strategies=[['1', '2'], ['1', '3'], ['1', '2', '3']])
        ]
    )]
)
def test_count_sorter_aggregation(input: List[List[GeneratedName]], expected: List[GeneratedName]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        sorter = CountSorter(config)

        sorted_names = sorter.sort(input)

        assert len(sorted_names) == len(expected)
        for name, expected in zip(sorted_names, expected):
            assert str(name) == str(expected)
            assert_applied_strategies_are_equal(name.applied_strategies, expected.applied_strategies)
