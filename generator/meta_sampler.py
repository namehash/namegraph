import logging
import random
from typing import Type
from ens_normalize import is_ens_normalized

from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.sampling import WeightedSorterWithOrder
from generator.sampling.round_robin_sampler import RoundRobinSampler
from generator.sampling.sampler import Sampler
from generator.input_name import InputName

logger = logging.getLogger('generator')


class MetaSampler:
    def get_weights(
            self,
            pipelines: tuple[Pipeline],
            type: str,
            lang: str = 'default',
            mode: str = 'full'
    ) -> dict[Pipeline, float]:  # TODO cache?
        """
        Return weights for pipelines for given type and language based on pipeline config.
        """

        weights = {}
        for pipeline in pipelines:
            pipeline_weights = pipeline.weights
            try:
                pipeline_weight = pipeline_weights[type][lang]
            except KeyError:
                pipeline_weight = pipeline_weights[type]['default']

            weights_multiplier = pipeline.mode_weights_multiplier.get(mode, None)
            if weights_multiplier is None and mode.startswith('grouped_'):
                # use ungrouped mode weights_multiplier as default (if key 'grouped_{mode}' does not exist)
                weights_multiplier = pipeline.mode_weights_multiplier.get(mode.removeprefix('grouped_'), 1.0)
            elif weights_multiplier is None:
                weights_multiplier = 1.0
            weights[pipeline] = pipeline_weight * weights_multiplier
        return weights

    def get_sampler(self, sampler: str) -> Type[Sampler]:
        """
        Return sampler by a name.
        """
        match sampler:
            case 'round-robin':
                return RoundRobinSampler
            case 'weighted-sampling':
                return WeightedSorterWithOrder
            case _:
                raise ValueError(f'{sampler} is unavailable')

    def __init__(self, config, pipelines: list[Pipeline]):
        self.config = config
        self.domains = Domains(config)
        self.pipelines = pipelines

    def get_global_limits(self, mode: str, min_suggestions: int):
        global_limits = {}
        for pipeline in self.pipelines:
            limit = pipeline.global_limits.get(mode, None)
            if limit is None and mode.startswith('grouped_'):
                # use ungrouped mode limit as default limit (if key 'grouped_{mode}' does not exist)
                limit = pipeline.global_limits.get(mode.removeprefix('grouped_'), None)
            if isinstance(limit, float):
                limit = int(min_suggestions * limit)
            global_limits[pipeline.pipeline_name] = limit
        return global_limits

    def sample(self, name: InputName, sorter_name: str, min_suggestions: int, max_suggestions: int,
               min_available_fraction: float) -> list[GeneratedName]:
        min_available_required = int(min_suggestions * min_available_fraction)

        mode = name.params.get('mode', 'full')

        types_lang_weights = {}
        interpretation_weights = {}
        for type_lang, weight in name.types_probabilities.items():
            if weight > 0:
                types_lang_weights[type_lang] = weight
                interpretation_weights[type_lang] = {}
                for interpretation in name.interpretations[type_lang]:
                    interpretation_weights[type_lang][interpretation] = interpretation.in_type_probability

        global_limits = self.get_global_limits(mode, min_suggestions)

        sorters = {}
        for (interpretation_type, lang), interpretations in name.interpretations.items():
            for interpretation in interpretations:
                weights = self.get_weights(tuple(self.pipelines), interpretation_type, lang, mode)
                # logger.info(f'weights {weights}')
                sorters[interpretation] \
                    = self.get_sampler(sorter_name)(self.config, self.pipelines, weights)

        available_added = 0

        all_suggestions = []
        all_suggestions_str = set()
        joined_input_name = name.input_name.replace(' ', '')

        while True:
            if len(all_suggestions) >= max_suggestions or not types_lang_weights:
                break

            # sample interpretation
            sampled_type_lang = random.choices(
                list(types_lang_weights.keys()),
                weights=list(types_lang_weights.values())
            )[0]

            sampled_interpretation = random.choices(
                list(interpretation_weights[sampled_type_lang].keys()),
                weights=list(interpretation_weights[sampled_type_lang].values())
            )[0]

            while True:
                try:
                    slots_left = max_suggestions - len(all_suggestions)
                    if slots_left <= 0:
                        break

                    # sample and run pipeline
                    sampled_pipeline = next(sorters[sampled_interpretation])

                    # logger.info(f'global_limits {global_limits[sampled_pipeline.pipeline_name]}')
                    if global_limits[sampled_pipeline.pipeline_name] is not None and \
                            global_limits[sampled_pipeline.pipeline_name] == 0:
                        sorters[sampled_interpretation].pipeline_used(sampled_pipeline)
                        continue

                    suggestions = sampled_pipeline.apply(name, sampled_interpretation)

                    try:
                        suggestion = next(suggestions)
                        suggestion.status = self.domains.get_name_status(str(suggestion))
                        # skip until it is not a duplicate and until it is "available" in case there are
                        # just enough free slots left to fulfill minimal available number of suggestions requirement
                        while True:
                            while str(suggestion) in all_suggestions_str or str(suggestion) == joined_input_name \
                                    or (suggestion.status != Domains.AVAILABLE
                                        and available_added + slots_left <= min_available_required):
                                suggestion = next(suggestions)
                                suggestion.status = self.domains.get_name_status(str(suggestion))
                            if not is_ens_normalized(str(suggestion)):
                                # log suggestions which are not ens normalized
                                logger.warning(f"suggestion not ens-normalized: '{str(suggestion)}'; "
                                               f"metadata: {suggestion.dict()}")
                                suggestion = next(suggestions)
                                suggestion.status = self.domains.get_name_status(str(suggestion))
                            else:
                                break
                    except StopIteration:
                        # in case the suggestions have run out we simply mark the pipeline as empty
                        # and proceed to sample another non-empty pipeline
                        sorters[sampled_interpretation].pipeline_used(sampled_pipeline)
                        continue

                    # on the other hand, if the suggestion is alright, then we add it to the list
                    # and update corresponding counters and variables
                    if suggestion.status == Domains.AVAILABLE:
                        available_added += 1

                    all_suggestions.append(suggestion)
                    all_suggestions_str.add(str(suggestion))
                    if global_limits[sampled_pipeline.pipeline_name] is not None:
                        global_limits[sampled_pipeline.pipeline_name] -= 1
                    break

                except StopIteration:
                    # removes entries from the sampling population because they are emptied
                    del interpretation_weights[sampled_type_lang][sampled_interpretation]
                    if not interpretation_weights[sampled_type_lang]:
                        del interpretation_weights[sampled_type_lang]
                        del types_lang_weights[sampled_type_lang]
                    break

        return all_suggestions

    def sample_grouped(self, name: InputName, sorter_name: str, min_suggestions: int, max_suggestions: int,
               min_available_fraction: float) -> list[GeneratedName]:
        min_available_required = int(min_suggestions * min_available_fraction)

        mode = name.params.get('mode', 'full')

        types_lang_weights = {}
        interpretation_weights = {}
        for type_lang, weight in name.types_probabilities.items():
            if weight > 0:
                types_lang_weights[type_lang] = weight
                interpretation_weights[type_lang] = {}
                for interpretation in name.interpretations[type_lang]:
                    interpretation_weights[type_lang][interpretation] = interpretation.in_type_probability

        global_limits = self.get_global_limits(mode, max_suggestions)
        print('global_limits', global_limits)

        sorters = {}
        for (interpretation_type, lang), interpretations in name.interpretations.items():
            for interpretation in interpretations:
                weights = self.get_weights(tuple(self.pipelines), interpretation_type, lang, mode)
                # logger.info(f'weights {weights}')
                sorters[interpretation] \
                    = self.get_sampler(sorter_name)(self.config, self.pipelines, weights)

        available_added = 0

        all_suggestions = []
        all_suggestions_str = set()
        joined_input_name = name.input_name.replace(' ', '')


        print(types_lang_weights)
        print(interpretation_weights)
        print(sorters)
        while True:
            if len(all_suggestions) >= max_suggestions or not types_lang_weights:
                break

            # sample interpretation
            sampled_type_lang = random.choices(
                list(types_lang_weights.keys()),
                weights=list(types_lang_weights.values())
            )[0]

            sampled_interpretation = random.choices(
                list(interpretation_weights[sampled_type_lang].keys()),
                weights=list(interpretation_weights[sampled_type_lang].values())
            )[0]
            print(sampled_type_lang, sampled_interpretation)
            while True:
                try:
                    slots_left = max_suggestions - len(all_suggestions)
                    if slots_left <= 0:
                        break

                    # sample and run pipeline
                    sampled_pipeline = next(sorters[sampled_interpretation])
                    print('sampled_pipeline', sampled_pipeline)

                    # logger.info(f'global_limits {global_limits[sampled_pipeline.pipeline_name]}')
                    if global_limits[sampled_pipeline.pipeline_name] is not None and \
                            global_limits[sampled_pipeline.pipeline_name] == 0:
                        sorters[sampled_interpretation].pipeline_used(sampled_pipeline)
                        print('global limit reached')
                        continue

                    suggestions = sampled_pipeline.apply(name, sampled_interpretation)

                    try:
                        suggestion = next(suggestions)
                        print('-', suggestion)
                        suggestion.status = self.domains.get_name_status(str(suggestion))
                        # skip until it is not a duplicate and until it is "available" in case there are
                        # just enough free slots left to fulfill minimal available number of suggestions requirement
                        while True:
                            while str(suggestion) in all_suggestions_str or str(suggestion) == joined_input_name \
                                    or (suggestion.status != Domains.AVAILABLE
                                        and available_added + slots_left <= min_available_required):
                                suggestion = next(suggestions)
                                print('-', suggestion)
                                suggestion.status = self.domains.get_name_status(str(suggestion))
                            if not is_ens_normalized(str(suggestion)):
                                # log suggestions which are not ens normalized
                                logger.warning(f"suggestion not ens-normalized: '{str(suggestion)}'; "
                                               f"metadata: {suggestion.dict()}")
                                suggestion = next(suggestions)
                                suggestion.status = self.domains.get_name_status(str(suggestion))
                            else:
                                break
                    except StopIteration:
                        # in case the suggestions have run out we simply mark the pipeline as empty
                        # and proceed to sample another non-empty pipeline
                        print('pipeline empty')
                        sorters[sampled_interpretation].pipeline_used(sampled_pipeline)
                        continue

                    # on the other hand, if the suggestion is alright, then we add it to the list
                    # and update corresponding counters and variables
                    if suggestion.status == Domains.AVAILABLE:
                        available_added += 1

                    all_suggestions.append(suggestion)
                    all_suggestions_str.add(str(suggestion))
                    if global_limits[sampled_pipeline.pipeline_name] is not None:
                        global_limits[sampled_pipeline.pipeline_name] -= 1
                    break

                except StopIteration:
                    # removes entries from the sampling population because they are emptied
                    del interpretation_weights[sampled_type_lang][sampled_interpretation]
                    if not interpretation_weights[sampled_type_lang]:
                        del interpretation_weights[sampled_type_lang]
                        del types_lang_weights[sampled_type_lang]
                    break

        return all_suggestions