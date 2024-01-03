import logging
from typing import Type, Callable
from ens_normalize import is_ens_normalized

from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.sampling import WeightedSorterWithOrder
from generator.sampling.round_robin_sampler import RoundRobinSampler
from generator.sampling.sampler import Sampler
from generator.input_name import InputName
from generator.thread_utils import init_seed_for_thread, get_random_rng


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

    def get_global_limits(self, mode: str, min_suggestions: int, category_limits: bool = False) -> dict[str, int]:
        """
        Return global limits for pipelines based on pipeline config. If category_limits is True, then
        category_limits are returned instead of global_limits.
        """
        global_limits = {}
        for pipeline in self.pipelines:
            if category_limits:
                limit = pipeline.category_limits.get(mode, None)
            else:
                limit = pipeline.global_limits.get(mode, None)
                if limit is None and mode.startswith('grouped_'):
                    # use ungrouped mode limit as default limit (if key 'grouped_{mode}' does not exist)
                    limit = pipeline.global_limits.get(mode.removeprefix('grouped_'), None)
            if isinstance(limit, float):
                limit = int(min_suggestions * limit)
            global_limits[pipeline.pipeline_name] = limit
        return global_limits

    async def sample(
            self,
            name: InputName,
            sorter_name: str,
            min_suggestions: int,
            max_suggestions: int,
            min_available_fraction: float,
            category_endpoint: bool = False,
            is_already_sampled: Callable[[str], bool] = lambda x: False,
    ) -> list[GeneratedName]:
        min_available_required = int(min_suggestions * min_available_fraction)

        init_seed_for_thread(seed_label=name.input_name)  # init random generators for a thread

        mode = name.params.get('mode', 'full')

        types_lang_weights = {}
        interpretation_weights = {}
        for type_lang, weight in name.types_probabilities.items():
            if weight > 0:
                types_lang_weights[type_lang] = weight
                interpretation_weights[type_lang] = {}
                for interpretation in name.interpretations[type_lang]:
                    interpretation_weights[type_lang][interpretation] = interpretation.in_type_probability

        if category_endpoint:
            global_limits = self.get_global_limits(mode, max_suggestions, category_limits=True)
        else:
            global_limits = self.get_global_limits(mode, min_suggestions)
        logger.debug(f'global_limits {global_limits}')

        sorters = {}
        for (interpretation_type, lang), interpretations in name.interpretations.items():
            for interpretation in interpretations:
                weights = self.get_weights(tuple(self.pipelines), interpretation_type, lang, mode)
                # logger.debug(f'weights {weights}')
                sorters[interpretation] \
                    = self.get_sampler(sorter_name)(self.config, self.pipelines, weights)

        available_added = 0

        all_suggestions = []
        all_suggestions_str = set()
        joined_input_name = name.input_name.replace(' ', '')

        rng = get_random_rng()

        while True:
            if len(all_suggestions) >= max_suggestions or not types_lang_weights:
                break

            # sample interpretation
            sampled_type_lang = rng.choices(
                list(types_lang_weights.keys()),
                weights=list(types_lang_weights.values())
            )[0]

            sampled_interpretation = rng.choices(
                list(interpretation_weights[sampled_type_lang].keys()),
                weights=list(interpretation_weights[sampled_type_lang].values())
            )[0]

            # logger.debug(f'sampled_type_lang {sampled_type_lang} sampled_interpretation {sampled_interpretation}')

            while True:
                try:
                    slots_left = max_suggestions - len(all_suggestions)
                    if slots_left <= 0:
                        break

                    # sample and run pipeline
                    sampled_pipeline = next(sorters[sampled_interpretation])
                    logger.debug(f'sampled_pipeline {sampled_pipeline.pipeline_name}')

                    # logger.debug(f'global_limits {global_limits[sampled_pipeline.pipeline_name]}')
                    if global_limits[sampled_pipeline.pipeline_name] is not None and \
                            global_limits[sampled_pipeline.pipeline_name] == 0:
                        sorters[sampled_interpretation].pipeline_used(sampled_pipeline)
                        logger.debug(f'global_limits reached by {sampled_pipeline.pipeline_name}')
                        continue

                    suggestions = await sampled_pipeline.apply(name, sampled_interpretation)

                    try:
                        suggestion = next(suggestions)
                        suggestion.status = self.domains.get_name_status(str(suggestion))
                        logger.debug(f'Pipeline: {sampled_pipeline.pipeline_name} sampled suggestion: {suggestion}')

                        # skip until it is not a duplicate and until it is "available" in case there are
                        # just enough free slots left to fulfill minimal available number of suggestions requirement
                        while True:
                            while str(suggestion) in all_suggestions_str or str(suggestion) == joined_input_name \
                                    or (suggestion.status != Domains.AVAILABLE
                                        and available_added + slots_left <= min_available_required):
                                logger.debug(
                                    f'suggestion is duplicated or the same as input (or unavailable): {suggestion}')
                                suggestion = next(suggestions)
                                logger.debug(
                                    f'Pipeline: {sampled_pipeline.pipeline_name} sampled suggestion: {suggestion}')
                                suggestion.status = self.domains.get_name_status(str(suggestion))
                            if not is_ens_normalized(str(suggestion)):
                                # log suggestions which are not ens normalized
                                logger.warning(f"suggestion not ens-normalized: '{str(suggestion)}'; "
                                               f"metadata: {suggestion.dict()}")
                                suggestion = next(suggestions)
                                logger.debug(
                                    f'Pipeline: {sampled_pipeline.pipeline_name} sampled suggestion: {suggestion}')
                                suggestion.status = self.domains.get_name_status(str(suggestion))
                            elif is_already_sampled(str(suggestion)):
                                logger.debug(
                                    f'suggestion is already sampled (in another sampler): {suggestion}')
                                suggestion = next(suggestions)
                                logger.debug(
                                    f'Pipeline: {sampled_pipeline.pipeline_name} sampled suggestion: {suggestion}')
                                suggestion.status = self.domains.get_name_status(str(suggestion))
                            else:
                                break
                    except StopIteration:
                        # in case the suggestions have run out we simply mark the pipeline as empty
                        # and proceed to sample another non-empty pipeline
                        logger.debug(f'pipeline {sampled_pipeline.pipeline_name} is empty')
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
                    logger.debug(f'removing interpretation')
                    del interpretation_weights[sampled_type_lang][sampled_interpretation]
                    if not interpretation_weights[sampled_type_lang]:
                        del interpretation_weights[sampled_type_lang]
                        del types_lang_weights[sampled_type_lang]
                    break

        return all_suggestions
