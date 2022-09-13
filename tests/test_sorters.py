from typing import List
import itertools

import pytest
from pytest import mark
from hydra import initialize, compose

from generator.generated_name import GeneratedName
from generator.sorting import CountSorter, RoundRobinSorter, LengthSorter, WeightedSamplingSorter

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

        sorted_strings = [str(gn) for gn in sorter.sort(input)]
        assert sorted_strings == expected_strings


@mark.parametrize(
    "input, expected_strings",
    [(
        [
            [GeneratedName(('a' * 15)), GeneratedName(('f' * 10))],
            [GeneratedName(('vv'))],
            [GeneratedName(('dddd'))],
            [GeneratedName(('y' * 4, 'y' * 3))],
            [GeneratedName(('jjj', 'j', 'j'))]
        ],
        ['v'*2, 'd'*4, 'j'*5, 'y'*7, 'f'*10, 'a'*15]
    )]
)
def test_length_sorter(input: List[List[GeneratedName]], expected_strings: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        sorter = LengthSorter(config)

        sorted_strings = [str(gn) for gn in sorter.sort(input)]
        assert sorted_strings == expected_strings


@mark.parametrize(
    "input, expected_strings",
    [
        (
            [[GeneratedName(('a',), pipeline_name='permute'),
              GeneratedName(('b',), pipeline_name='permute'),
              GeneratedName(('c',), pipeline_name='permute')]],
            ['a', 'b', 'c']
        ),
    ]
)
def test_weighted_sampling_sorter(input: List[List[GeneratedName]], expected_strings: List[str]):
    with initialize(version_base=None, config_path='../conf/'):
        config = compose(config_name='test_config')
        sorter = WeightedSamplingSorter(config)

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


@mark.parametrize(
    "input, expected",
    [(
        [
            [GeneratedName(('aa'), applied_strategies=[['1', '2'], ['1', '3']])],
            [GeneratedName(('aa'), applied_strategies=[['1', '2', '3']]),
             GeneratedName(('b'), applied_strategies=[['2']])],
            [GeneratedName(('b'), applied_strategies=[['2', '3'], ['2']])],
            [GeneratedName(('ccc'), applied_strategies=[['2'], ['5', '6']])],
            [GeneratedName(('ccc'), applied_strategies=[['1', '4'], ['5', '6']])]
        ],
        [
            GeneratedName(('b'), applied_strategies=[['2'], ['2', '3']]),
            GeneratedName(('aa'), applied_strategies=[['1', '2'], ['1', '3'], ['1', '2', '3']]),
            GeneratedName(('ccc'), applied_strategies=[['1', '4'], ['2'], ['5', '6']]),
        ]
    )]
)
def test_length_sorter_aggregation(input: List[List[GeneratedName]], expected: List[GeneratedName]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        sorter = LengthSorter(config)

        sorted_names = sorter.sort(input)

        assert len(sorted_names) == len(expected)
        for name, expected in zip(sorted_names, expected):
            assert str(name) == str(expected)
            assert_applied_strategies_are_equal(name.applied_strategies, expected.applied_strategies)


@mark.parametrize(
    "input, expected",
    [
        (
            [
                [GeneratedName(('a',), pipeline_name='permute', applied_strategies=[['1'], ['2']]),
                 GeneratedName(('b',), pipeline_name='permute', applied_strategies=[['2'], ['1']]),
                 GeneratedName(('a',), pipeline_name='permute', applied_strategies=[['3']])]
            ],
            [
                GeneratedName(('a',), applied_strategies=[['1'], ['2'], ['3']]),
                GeneratedName(('b',), applied_strategies=[['2'], ['1']])
            ]
        ),
    ]
)
def test_weighted_sampling_sorter_aggregation(input: List[List[GeneratedName]], expected: List[GeneratedName]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        sorter = WeightedSamplingSorter(config)

        sorted_names = sorter.sort(input)

        assert len(sorted_names) == len(expected)
        for name, expected in zip(sorted_names, expected):
            assert str(name) == str(expected)
            assert_applied_strategies_are_equal(name.applied_strategies, expected.applied_strategies)


@mark.slow
@mark.parametrize(
    "overrides",
    [
        ("sorting.weighted_sampling.use_softmax=false",),
        ("sorting.weighted_sampling.use_softmax=true",)
    ]
)
def test_weighted_sampling_sorter_stress(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)

        with open(config.app.internet_domains, 'r', encoding='utf-8') as f:
            words = [d for d in itertools.islice(iter(f), 49999)] + ['pumpkins']

        generated_names = []
        for (from_idx, to_idx), pipeline_name, generator_name in [((0, 10000), 'permute', 'PermuteGenerator'),
                                                                  ((10000, 20000), 'w2v', 'W2VGenerator'),
                                                                  ((20000, 30000), 'random', 'RandomGenerator'),
                                                                  ((30000, 40000), 'synonyms', 'WordnetSynonymsGenerator'),
                                                                  ((40000, 50000), 'suffix', 'SuffixGenerator')]:
            generated_names.append([
                GeneratedName((word,), pipeline_name=pipeline_name, applied_strategies=[[generator_name]])
                for word in words[from_idx:to_idx]
            ])

        sorter = WeightedSamplingSorter(config)
        sorted_names = sorter.sort(generated_names)


@mark.slow
@mark.parametrize(
    "overrides",
    [
        ("sorting.weighted_sampling.use_softmax=false",),
        ("sorting.weighted_sampling.use_softmax=true",)
    ]
)
def test_weighted_sampling_sorter_stress2(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        sorter = WeightedSamplingSorter(config)
        sorted_names = sorter.sort([[
            GeneratedName(('abasariatic',), pipeline_name='random', applied_strategies=[['RandomGenerator']])
            for _ in range(10000)
        ]])


@mark.slow
@mark.parametrize(
    "overrides",
    [
        ("sorting.weighted_sampling.use_softmax=false",),
        ("sorting.weighted_sampling.use_softmax=true",)
    ]
)
def test_weighted_sampling_sorter_weights(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config", overrides=overrides)

        generated_names = []
        for pipeline_name in [
            'permute',
            'suffix',
            'prefix',
            'synonyms',
            'w2v',
            'categories-no-tokenizer',
            'secondary',
            'wiki2v',
            'substring',
        ]:
            generated_names.append([
                GeneratedName((pipeline_name + str(i),), pipeline_name=pipeline_name)
                for i in range(100)]
            )

        sorter = WeightedSamplingSorter(config)
        sorted_names = sorter.sort(generated_names)
        print(sorted_names[:30])
