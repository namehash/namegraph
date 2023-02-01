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
        config = compose(config_name='test_config_new')
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
        config = compose(config_name="test_config_new")
        sorter = WeightedSamplingSorter(config)

        sorted_names = sorter.sort(input)

        assert len(sorted_names) == len(expected)
        for name, expected in zip(sorted_names, expected):
            assert str(name) == str(expected)
            assert_applied_strategies_are_equal(name.applied_strategies, expected.applied_strategies)


@mark.slow
def test_weighted_sampling_sorter_stress():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")

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
def test_weighted_sampling_sorter_stress2():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        sorter = WeightedSamplingSorter(config)
        sorted_names = sorter.sort([[
            GeneratedName(('abasariatic',), pipeline_name='random', applied_strategies=[['RandomGenerator']])
            for _ in range(10000)
        ]])


@mark.slow
def test_weighted_sampling_sorter_weights():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")

        generated_names = []
        for pipeline_name in [
            'permute',
            'suffix',
            'prefix',
            'synonyms',
            'w2v',
            'categories-no-tokenizer',
            'on_sale',
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


@mark.parametrize(
    "overrides,input_names,expected_strings,min_suggestions,max_suggestions",
    [
        (
            # simple situation: first 2 names in the sorted array satisfies the obligation
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'),   GeneratedName(('ccc',), category='on_sale')],
                [GeneratedName(('dddd',), category='on_sale'),     GeneratedName(('bb', ), category='available')]
            ], ['a', 'bb', 'ccc'], 2, 3
        ),
        (
            # we need 2 available names, after the second one we have one place left and one available available,
            # so we must take it, disregarding the next names in the line
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'), GeneratedName(('ccc',), category='on_sale')],
                [GeneratedName(('dddd',), category='available'), GeneratedName(('bb', ), category='advertised')]
            ], ['a', 'bb', 'dddd'], 2, 3
        ),
        (
            # test for off-by-one error while counting used available names and left available names
            ["app.min_available_fraction=1.5"], [
                [GeneratedName(('a',),     category='available'), GeneratedName(('ccc',), category='on_sale')],
                [GeneratedName(('dddd',),  category='available'), GeneratedName(('bb', ), category='advertised')],
                [GeneratedName(('eeeee',), category='taken')]
            ], ['a', 'bb', 'dddd'], 2, 3
        ),
        (
            # disregarding the fact that the last possible available name is the last, max_suggestions allows us
            # to take all the generated names, so we keep them in the order defined by the sorter
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'), GeneratedName(('ccc',), category='on_sale')],
                [GeneratedName(('dddd',), category='available'), GeneratedName(('bb', ), category='advertised')]
            ], ['a', 'bb', 'ccc', 'dddd'], 2, 4
        ),
        (
            # we need 3 available names, but have only 2 available, so we take all the names in the order defined by
            # sorter, until there is just enough place left to take all the rest of possible available names
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'), GeneratedName(('ccc',), category='on_sale')],
                [GeneratedName(('dddd',), category='available'), GeneratedName(('bb', ), category='advertised')]
            ], ['a', 'bb', 'dddd'], 3, 3
        ),
        (
            # same as above, we need 2, but have only 1, so we take it as the last element, if we haven't met it yet
            # (and it is somewhere further away in the order defined by the sorter)
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='taken'),      GeneratedName(('ccc',), category='available')],
                [GeneratedName(('dddd',), category='advertised'), GeneratedName(('bb', ), category='advertised')]
            ], ['a', 'ccc'], 2, 2
        ),
        (
            # we need 2 available names, and have 2 available, but it is a duplicate, so only 1 is left, so we take it,
            # since it is first in the order, and the take the next from the line
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'),  GeneratedName(('bb',), category='advertised')],
                [GeneratedName(('dddd',), category='advertised'), GeneratedName(('a', ), category='available')]
            ], ['a', 'bb'], 2, 2
        ),
        (
            # we need 2 available names, but none of them would be taken if we followed the order defined by the sorter,
            # and we notice that we need 2, so we take 2 of the in the order defined by the sorter
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='taken'),     GeneratedName(('ccc',), category='available')],
                [GeneratedName(('dddd',), category='available'), GeneratedName(('bb', ), category='advertised')]
            ], ['ccc', 'dddd'], 2, 2
        ),
        (
            # same as above, but we have one place more, so we take one name from the line defined by the sorter
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='taken'),     GeneratedName(('ccc',), category='available')],
                [GeneratedName(('dddd',), category='available'), GeneratedName(('bb', ), category='advertised')]
            ], ['a', 'ccc', 'dddd'], 3, 3
        ),
    ],
)
def test_available_fraction_obligation_length_sorter(overrides: List[str],
                                                     input_names: List[List[GeneratedName]],
                                                     expected_strings: List[str],
                                                     min_suggestions: int,
                                                     max_suggestions: int):

    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        sorter = LengthSorter(config)

        sorted_strings = [str(gn) for gn in sorter.sort(input_names, min_suggestions, max_suggestions)]
        assert sorted_strings == expected_strings


@mark.parametrize(
    "overrides,input_names,expected_strings,min_suggestions,max_suggestions",
    [
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'), GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),    GeneratedName(('dddd', ), category='available')]
            ], ['a', 'bb', 'ccc', 'dddd'], 2, 4
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'), GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),    GeneratedName(('dddd', ), category='available')]
            ], ['a', 'bb', 'dddd'], 2, 3
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),   category='available'), GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='taken'),     GeneratedName(('dddd', ), category='available')]
            ], ['a', 'dddd'], 2, 2
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),    category='available'), GeneratedName(('bb',), category='advertised'),
                 GeneratedName(('ccc',), category='on_sale'),    GeneratedName(('a', ), category='available')]
            ], ['a', 'bb'], 2, 2
        ),
    ],
)
def test_available_fraction_obligation_weighted_sampling_sorter(overrides: List[str],
                                                                input_names: List[List[GeneratedName]],
                                                                expected_strings: List[str],
                                                                min_suggestions: int,
                                                                max_suggestions: int):

    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        sorter = WeightedSamplingSorter(config)

        sorted_strings = [str(gn) for gn in sorter.sort(input_names, min_suggestions, max_suggestions)]
        assert sorted_strings == expected_strings


@mark.parametrize(
    "overrides,input_names,expected_strings,min_suggestions,max_suggestions",
    [
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),   category='available'), GeneratedName(('bb',),    category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),   GeneratedName(('dddd', ), category='taken')],

                [GeneratedName(('e',), category='advertised'), GeneratedName(('ff',),   category='taken'),
                 GeneratedName(('a',), category='available'),  GeneratedName(('hhhh',), category='available')]
            ], ['a', 'hhhh'], 2, 2
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('ddd',), category='advertised'), GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),    GeneratedName(('a', ), category='taken')],

                [GeneratedName(('e',),   category='advertised'), GeneratedName(('ff',),   category='taken'),
                 GeneratedName(('a',),   category='available'),  GeneratedName(('hhhh',), category='available')],

                [GeneratedName(('iii',), category='advertised'), GeneratedName(('kk',), category='on_sale'),
                 GeneratedName(('jjj',), category='on_sale'),    GeneratedName(('m', ), category='taken')],
            ], ['a', 'hhhh'], 2, 2
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('ddd',), category='available'), GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),   GeneratedName(('a', ), category='taken')],

                [GeneratedName(('e',),   category='advertised'), GeneratedName(('ff',),   category='taken'),
                 GeneratedName(('a',),   category='available'),  GeneratedName(('hhhh',), category='available')],

                [GeneratedName(('iii',), category='available'), GeneratedName(('kk',), category='on_sale'),
                 GeneratedName(('jjj',), category='on_sale'),   GeneratedName(('m', ), category='taken')],
            ], ['a', 'hhhh', 'ddd', 'iii'], 4, 4
        ),
    ]
)
def test_available_fraction_obligation_weighted_sampling_sorter_no_order(overrides: List[str],
                                                                         input_names: List[List[GeneratedName]],
                                                                         expected_strings: List[str],
                                                                         min_suggestions: int,
                                                                         max_suggestions: int):

    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        sorter = WeightedSamplingSorter(config)

        sorted_strings = [str(gn) for gn in sorter.sort(input_names, min_suggestions, max_suggestions)]
        assert set(sorted_strings) == set(expected_strings)


@mark.parametrize(
    "overrides,input_names,min_suggestions,max_suggestions,min_expected_available,max_expected_available",
    [
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),   category='available'),  GeneratedName(('bb',),    category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),    GeneratedName(('dddd', ), category='taken'),
                 GeneratedName(('e',),   category='advertised'), GeneratedName(('ff',),    category='taken'),
                 GeneratedName(('l',),   category='on_sale'),   GeneratedName(('hhhh',),   category='advertised')]
            ], 4, 5, 1, 1
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),   category='on_sale'),    GeneratedName(('bb',),    category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),    GeneratedName(('dddd', ), category='taken'),
                 GeneratedName(('e',),   category='advertised'), GeneratedName(('ff',),    category='taken'),
                 GeneratedName(('l',),   category='on_sale'),    GeneratedName(('hhhh',),  category='advertised')]
            ], 4, 5, 0, 0
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('a',),   category='available'), GeneratedName(('bb',),    category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),   GeneratedName(('dddd', ), category='taken')],

                [GeneratedName(('e',), category='advertised'),  GeneratedName(('ff',),   category='taken'),
                 GeneratedName(('a',), category='available'),   GeneratedName(('hhhh',), category='available')]
            ], 2, 2, 2, 2
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('ddd',), category='advertised'), GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),    GeneratedName(('a', ), category='taken')],

                [GeneratedName(('e',),   category='advertised'), GeneratedName(('ff',),   category='taken'),
                 GeneratedName(('a',),   category='advertised'), GeneratedName(('hhhh',), category='on_sale')],

                [GeneratedName(('iii',), category='taken'),    GeneratedName(('kk',), category='on_sale'),
                 GeneratedName(('jjj',), category='on_sale'),  GeneratedName(('m', ), category='taken')],
            ], 7, 9, 0, 0
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('ddd',), category='available'), GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),   GeneratedName(('a', ), category='taken')],

                [GeneratedName(('e',),   category='advertised'), GeneratedName(('ff',),   category='taken'),
                 GeneratedName(('a',),   category='available'),  GeneratedName(('hhhh',), category='available')],

                [GeneratedName(('iii',), category='available'),  GeneratedName(('kk',), category='on_sale'),
                 GeneratedName(('jjj',), category='on_sale'),    GeneratedName(('m', ), category='taken')],
            ], 2, 2, 2, 2
        ),
        (
            #
            ["app.min_available_fraction=1.0"], [
                [GeneratedName(('ddd',), category='taken'),    GeneratedName(('bb',), category='on_sale'),
                 GeneratedName(('ccc',), category='on_sale'),  GeneratedName(('a', ), category='taken')],

                [GeneratedName(('e',),   category='advertised'), GeneratedName(('ff',),   category='taken'),
                 GeneratedName(('a',),   category='on_sale'),    GeneratedName(('hhhh',), category='available')],

                [GeneratedName(('iii',), category='advertised'), GeneratedName(('kk',), category='on_sale'),
                 GeneratedName(('jjj',), category='on_sale'),    GeneratedName(('m', ), category='taken')],
            ], 2, 5, 1, 1
        ),
    ]
)
def test_available_fraction_obligation_weighted_sampling_sorter_available_names_number(
        overrides: List[str],
        input_names: List[List[GeneratedName]],
        min_suggestions: int,
        max_suggestions: int,
        min_expected_available: int,
        max_expected_available: int
):

    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        sorter = WeightedSamplingSorter(config)

        available_names_set = {
            str(name)
            for sublist in input_names
            for name in sublist
            if name.category == 'available'
        }

        sorted_strings = [str(gn) for gn in sorter.sort(input_names, min_suggestions, max_suggestions)]
        assert len(sorted_strings) <= max_suggestions
        assert min_expected_available <= len(available_names_set & set(sorted_strings)) <= max_expected_available
