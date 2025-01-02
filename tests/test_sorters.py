from typing import List
import itertools

import pytest
from pytest import mark
from hydra import initialize, compose

from name_graph.domains import Domains
from name_graph.generated_name import GeneratedName
from name_graph.input_name import InputName, Interpretation
from name_graph.meta_sampler import MetaSampler
from name_graph.pipeline.pipeline_results_iterator import PipelineResultsIterator
from name_graph.sampling import RoundRobinSampler, WeightedSorterWithOrder, WeightedSorter


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


class PipelineMock():
    def __init__(self, pipeline_name, names, weight=1.0):
        self.pipeline_name = pipeline_name
        self.names = names
        self.iterator = PipelineResultsIterator(self.names)

        self.global_limits = {}
        self.weights = {'ngram': {'default': weight}}
        self.mode_weights_multiplier = {'full': 1}

    def apply(self, name: InputName = None, interpretation: Interpretation = None) -> PipelineResultsIterator:
        return self.iterator


def get_suggestions(sorter):
    result = []
    for pipeline in sorter:
        try:
            pri = pipeline.apply()
            gn = next(pri)
            result.append(gn)
        except StopIteration:
            sorter.pipeline_used(pipeline)
    return result


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
        config = compose(config_name="test_config_new")
        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input)]
        sorter = RoundRobinSampler(config, pipelines, None)

        result = get_suggestions(sorter)

        sorted_strings = [str(gn) for gn in result]
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
        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input)]
        sorter = WeightedSorter(config, pipelines, {pipeline: 1.0 for pipeline in pipelines})

        result = get_suggestions(sorter)

        sorted_strings = [str(gn) for gn in result]
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
def test_weighted_sampling_sorter_with_order(input: List[List[GeneratedName]], expected_strings: List[str]):
    with initialize(version_base=None, config_path='../conf/'):
        config = compose(config_name='test_config_new')
        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input)]
        sorter = WeightedSorterWithOrder(config, pipelines, {pipeline: 1.0 for pipeline in pipelines})

        result = get_suggestions(sorter)

        sorted_strings = [str(gn) for gn in result]
        assert sorted_strings == expected_strings


@mark.parametrize(
    "input, expected",
    [(
            [
                [GeneratedName(('a',), applied_strategies=[['1', '2'], ['1', '3']])],
                [GeneratedName(('a',), applied_strategies=[['1', '2', '3']]),
                 GeneratedName(('b',), applied_strategies=[['2']])],
                [GeneratedName(('b',), applied_strategies=[['2', '3']])],
                [GeneratedName(('b',), applied_strategies=[['2']])]
            ],
            [
                GeneratedName(('a',), applied_strategies=[['1', '2'], ['1', '3'], ['1', '2', '3']]),
                GeneratedName(('b',), applied_strategies=[['2'], ['2', '3']])
            ]
    )]
)
def test_round_robin_sorter_deduplication(input: List[List[GeneratedName]], expected: List[GeneratedName]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input)]

        params = {}
        params['min_suggestions'] = config.app.suggestions
        params['max_suggestions'] = config.app.suggestions
        params['min_available_fraction'] = config.app.min_available_fraction

        input_name = InputName('asd', params)
        input_name.add_type('ngram', 'en', 1.0)
        input_name.add_interpretation(Interpretation('ngram', 'en', ('asd',), 1.0))
        metasampler = MetaSampler(config, pipelines)
        all_suggestions = metasampler.sample(input_name, 'round-robin', min_suggestions=input_name.params[
            'min_suggestions'], max_suggestions=input_name.params['max_suggestions'],
                                             min_available_fraction=input_name.params['min_available_fraction'])

        sorted_strings = sorted([str(gn) for gn in all_suggestions])
        sorted_expected_strings = sorted([str(gn) for gn in expected])

        assert sorted_strings == sorted_expected_strings


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
def test_weighted_sampling_sorter_deduplication(input: List[List[GeneratedName]], expected: List[GeneratedName]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input)]

        params = {}
        params['min_suggestions'] = config.app.suggestions
        params['max_suggestions'] = config.app.suggestions
        params['min_available_fraction'] = config.app.min_available_fraction

        input_name = InputName('asd', params)
        input_name.add_type('ngram', 'en', 1.0)
        input_name.add_interpretation(Interpretation('ngram', 'en', ('asd',), 1.0))
        metasampler = MetaSampler(config, pipelines)
        all_suggestions = metasampler.sample(input_name, 'weighted-sampling', min_suggestions=input_name.params[
            'min_suggestions'], max_suggestions=input_name.params['max_suggestions'],
                                             min_available_fraction=input_name.params['min_available_fraction'])

        sorted_strings = sorted([str(gn) for gn in all_suggestions])
        sorted_expected_strings = sorted([str(gn) for gn in expected])

        assert sorted_strings == sorted_expected_strings


@mark.slow
def test_weighted_sampling_sorter_stress():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=["app.suggestions=100"])

        with open('data/top_internet_names.csv', 'r', encoding='utf-8') as f:
            words = [str(i) + d.strip() for i, d in enumerate(itertools.islice(iter(f), 49999))] + ['pumpkins']

        generated_names = []
        for (from_idx, to_idx), pipeline_name, generator_name in [((0, 10000), 'permute', 'PermuteGenerator'),
                                                                  ((10000, 20000), 'w2v', 'W2VGenerator'),
                                                                  ((20000, 30000), 'random', 'RandomGenerator'),
                                                                  ((30000, 40000), 'synonyms',
                                                                   'WordnetSynonymsGenerator'),
                                                                  ((40000, 50000), 'suffix', 'SuffixGenerator')]:
            generated_names.append([
                GeneratedName((word,), pipeline_name=pipeline_name, applied_strategies=[[generator_name]])
                for word in words[from_idx:to_idx]
            ])

        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(generated_names)]

        params = {}
        params['min_suggestions'] = config.app.suggestions
        params['max_suggestions'] = config.app.suggestions
        params['min_available_fraction'] = config.app.min_available_fraction

        input_name = InputName('asd', params)
        input_name.add_type('ngram', 'en', 1.0)
        input_name.add_interpretation(Interpretation('ngram', 'en', ('asd',), 1.0))
        metasampler = MetaSampler(config, pipelines)
        all_suggestions = metasampler.sample(input_name, 'weighted-sampling', min_suggestions=input_name.params[
            'min_suggestions'], max_suggestions=input_name.params['max_suggestions'],
                                             min_available_fraction=input_name.params['min_available_fraction'])
        assert len(all_suggestions) == config.app.suggestions


@mark.slow
def test_weighted_sampling_sorter_weights():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")

        pipeline_names = [
            'permute',
            'suffix',
            'prefix',
            'synonyms',
            'w2v',
            'categories-no-tokenizer',
            'on_sale',
            'wiki2v',
            'substring',
        ]
        generated_names = []
        for pipeline_name in pipeline_names:
            generated_names.append([
                GeneratedName((pipeline_name + str(i),), pipeline_name=pipeline_name)
                for i in range(100)]
            )

        pipelines = [PipelineMock(pipeline_name, names, weight=10 if pipeline_name == 'w2v' else 1) for
                     pipeline_name, names in
                     zip(pipeline_names, generated_names)]

        params = {}
        params['min_suggestions'] = config.app.suggestions
        params['max_suggestions'] = config.app.suggestions
        params['min_available_fraction'] = config.app.min_available_fraction

        input_name = InputName('asd', params)
        input_name.add_type('ngram', 'en', 1.0)
        input_name.add_interpretation(Interpretation('ngram', 'en', ('asd',), 1.0))
        metasampler = MetaSampler(config, pipelines)
        all_suggestions = metasampler.sample(input_name, 'weighted-sampling', min_suggestions=input_name.params[
            'min_suggestions'], max_suggestions=input_name.params['max_suggestions'],
                                             min_available_fraction=input_name.params['min_available_fraction'])
        assert len(all_suggestions) == config.app.suggestions

        print(all_suggestions[:30])


@mark.parametrize(
    "overrides,input_names,expected_strings,min_suggestions,max_suggestions",
    [
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('dddd',), category='available')]
                ], ['a', 'bb', 'ccc', 'dddd'], 2, 4
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('dddd',), category='available')]
                ], ['a', 'bb', 'dddd'], 2, 3
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='taken'), GeneratedName(('dddd',), category='available')]
                ], ['a', 'dddd'], 2, 2
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='available'), GeneratedName(('bb',), category='available'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('a',), category='available')]
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

        for sublist in input_names:
            for name in sublist:
                if name.status != 'available':
                    Domains(config).taken[str(name)] = 1.0

        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input_names)]

        params = {}
        params['min_suggestions'] = min_suggestions
        params['max_suggestions'] = max_suggestions
        params['min_available_fraction'] = config.app.min_available_fraction

        input_name = InputName('asd', params)
        input_name.add_type('ngram', 'en', 1.0)
        input_name.add_interpretation(Interpretation('ngram', 'en', ('asd',), 1.0))
        metasampler = MetaSampler(config, pipelines)
        all_suggestions = metasampler.sample(input_name, 'weighted-sampling', min_suggestions=input_name.params[
            'min_suggestions'], max_suggestions=input_name.params['max_suggestions'],
                                             min_available_fraction=input_name.params['min_available_fraction'])

        sorted_strings = sorted([str(gn) for gn in all_suggestions])

        assert sorted_strings == expected_strings


@mark.parametrize(
    "overrides,input_names,expected_strings,min_suggestions,max_suggestions",
    [
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('dddd',), category='taken')],

                    [GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('a',), category='available'), GeneratedName(('hhhh',), category='available')]
                ], ['a', 'hhhh'], 2, 2
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('ddd',), category='taken'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('a',), category='available')],

                    [GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('a',), category='available'), GeneratedName(('hhhh',), category='available')],

                    [GeneratedName(('iii',), category='taken'), GeneratedName(('kk',), category='on_sale'),
                     GeneratedName(('jjj',), category='on_sale'), GeneratedName(('m',), category='taken')],
                ], ['a', 'hhhh'], 2, 2
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('ddd',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('a',), category='available')],

                    [GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('a',), category='available'), GeneratedName(('hhhh',), category='available')],

                    [GeneratedName(('iii',), category='available'), GeneratedName(('kk',), category='on_sale'),
                     GeneratedName(('jjj',), category='on_sale'), GeneratedName(('m',), category='taken')],
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

        for sublist in input_names:
            for name in sublist:
                if name.status != 'available':
                    Domains(config).taken[str(name)] = 1.0

        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input_names)]

        params = {}
        params['min_suggestions'] = min_suggestions
        params['max_suggestions'] = max_suggestions
        params['min_available_fraction'] = config.app.min_available_fraction

        input_name = InputName('asd', params)
        input_name.add_type('ngram', 'en', 1.0)
        input_name.add_interpretation(Interpretation('ngram', 'en', ('asd',), 1.0))
        metasampler = MetaSampler(config, pipelines)
        all_suggestions = metasampler.sample(input_name, 'weighted-sampling', min_suggestions=input_name.params[
            'min_suggestions'], max_suggestions=input_name.params['max_suggestions'],
                                             min_available_fraction=input_name.params['min_available_fraction'])

        sorted_strings = sorted([str(gn) for gn in all_suggestions])

        assert set(sorted_strings) == set(expected_strings)


@mark.parametrize(
    "overrides,input_names,min_suggestions,max_suggestions,min_expected_available,max_expected_available",
    [
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('dddd',), category='taken'),
                     GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('l',), category='on_sale'), GeneratedName(('hhhh',), category='taken')]
                ], 4, 5, 1, 1
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='on_sale'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('dddd',), category='taken'),
                     GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('l',), category='on_sale'), GeneratedName(('hhhh',), category='taken')]
                ], 4, 5, 0, 0
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('a',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('dddd',), category='taken')],

                    [GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('a',), category='available'), GeneratedName(('hhhh',), category='available')]
                ], 2, 2, 2, 2
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('ddd',), category='taken'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('a',), category='taken')],

                    [GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('a',), category='taken'), GeneratedName(('hhhh',), category='on_sale')],

                    [GeneratedName(('iii',), category='taken'), GeneratedName(('kk',), category='on_sale'),
                     GeneratedName(('jjj',), category='on_sale'), GeneratedName(('m',), category='taken')],
                ], 7, 9, 0, 0
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('ddd',), category='available'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('a',), category='taken')],

                    [GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('a',), category='available'), GeneratedName(('hhhh',), category='available')],

                    [GeneratedName(('iii',), category='available'), GeneratedName(('kk',), category='on_sale'),
                     GeneratedName(('jjj',), category='on_sale'), GeneratedName(('m',), category='taken')],
                ], 2, 2, 2, 2
        ),
        (
                #
                ["app.min_available_fraction=1.0"], [
                    [GeneratedName(('ddd',), category='taken'), GeneratedName(('bb',), category='on_sale'),
                     GeneratedName(('ccc',), category='on_sale'), GeneratedName(('a',), category='taken')],

                    [GeneratedName(('e',), category='taken'), GeneratedName(('ff',), category='taken'),
                     GeneratedName(('a',), category='on_sale'), GeneratedName(('hhhh',), category='available')],

                    [GeneratedName(('iii',), category='taken'), GeneratedName(('kk',), category='on_sale'),
                     GeneratedName(('jjj',), category='on_sale'), GeneratedName(('m',), category='taken')],
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

        available_names_set = {
            str(name)
            for sublist in input_names
            for name in sublist
            if name.status == 'available'
        }
        for sublist in input_names:
            for name in sublist:
                if name.status != 'available':
                    Domains(config).taken[str(name)] = 1.0

        pipelines = [PipelineMock(str(i), names) for i, names in enumerate(input_names)]

        params = {}
        params['min_suggestions'] = min_suggestions
        params['max_suggestions'] = max_suggestions
        params['min_available_fraction'] = config.app.min_available_fraction

        input_name = InputName('asd', params)
        input_name.add_type('ngram', 'en', 1.0)
        input_name.add_interpretation(Interpretation('ngram', 'en', ('asd',), 1.0))
        metasampler = MetaSampler(config, pipelines)
        all_suggestions = metasampler.sample(input_name, 'weighted-sampling', min_suggestions=input_name.params[
            'min_suggestions'], max_suggestions=input_name.params['max_suggestions'],
                                             min_available_fraction=input_name.params['min_available_fraction'])

        sorted_strings = sorted([str(gn) for gn in all_suggestions])

        assert len(sorted_strings) <= max_suggestions
        assert min_expected_available <= len(available_names_set & set(sorted_strings)) <= max_expected_available
