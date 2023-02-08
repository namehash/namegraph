import random, logging, math
from typing import List, Tuple, Dict, Collection

import numpy as np
import numpy.typing as npt
from omegaconf import DictConfig

from generator.domains import Domains
from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName
from generator.utils.aggregation import extend_and_aggregate

logger = logging.getLogger('generator')


def choice(probs: Collection) -> int:
    x = random.random()
    cum = 0.0
    for i, p in enumerate(probs):
        cum += p
        if x < cum:
            return i
    logger.warning(f'probabilities do not sum up to 1.0, but up to {cum}, so that randomized x = {x} is still greater, '
                   'thus choosing the last one')
    return len(probs) - 1


class WeightedSamplingSorter(Sorter):
    def __init__(self, config: DictConfig):
        super().__init__(config)
        sorter_config = self.config.sorting.weighted_sampling

        self.generator2weight = dict(sorter_config.weights)

        self.pipeline_weights: Dict[str, float] = {
            pipeline_name: max([self.generator2weight[generator] for generator in generators])
            for pipeline_name, generators in self._extract_pipelines_generators().items()
        }

    def _extract_pipelines_generators(self) -> Dict[str, Tuple[str, ...]]:
        generators_per_pipeline: Dict[str, Tuple[str, ...]] = dict()
        for definition in self.config.pipelines:
            generators_per_pipeline[definition.name] = (definition.generator,)

        return generators_per_pipeline

    def _calculate_possible_available_count(self,
                                          pipelines_suggestions: List[List[GeneratedName]],
                                          min_suggestions: int,
                                          min_available_fraction: float) -> int:

        # defining all the numbers regarding the available names result fraction requirement
        needed_available_count = int(math.ceil(min_available_fraction * min_suggestions))

        # checking if there is enough available names to cover the needed amount
        enough = False
        available_unique_suggestions = set()
        for pipeline_suggestions in pipelines_suggestions:

            for suggestion in pipeline_suggestions:
                if suggestion.status == Domains.AVAILABLE:
                    available_unique_suggestions.add(str(suggestion))
                    if len(available_unique_suggestions) >= needed_available_count:
                        enough = True
                        break

            if enough:
                break

        all_available_count = len(available_unique_suggestions)
        possible_available_count = min(needed_available_count, all_available_count)
        return possible_available_count

    def _get_pipeline_weights(self, pipelines_suggestions: List[List[GeneratedName]]) -> List[float]:
        pipeline_names = [
            suggestions[0].pipeline_name if suggestions else None
            for suggestions in pipelines_suggestions
        ]
        # TODO is it okay to set 1 as a default weight for unknown pipelines? there is an option to specify it in the config
        # TODO this simplifies testing a little, if the list is empty it will still get rewritten to 0.0
        pipeline_weights = [self.pipeline_weights.get(name, 1) for name in pipeline_names]
        return pipeline_weights

    def _normalize_weights(self, weights: List[float]) -> List[float]:
        summed = sum(weights)
        return [el / summed for el in weights]

    def sort(self,
             pipelines_suggestions: List[List[GeneratedName]],
             min_suggestions: int = None,
             max_suggestions: int = None,
             min_available_fraction: float = None) -> List[GeneratedName]:

        min_suggestions = min_suggestions or self.default_suggestions_count
        max_suggestions = max_suggestions or self.default_suggestions_count
        min_available_fraction = min_available_fraction or self.default_min_available_fraction

        possible_available_count = self._calculate_possible_available_count(pipelines_suggestions,
                                                                        min_suggestions,
                                                                        min_available_fraction)

        # defining variables required for the sampling itself and counting emptied pipelines
        empty_pipelines = 0
        available_used = 0
        sampling_only_available = False
        probabilities = self._get_pipeline_weights(pipelines_suggestions)

        # if there are any empty pipelines we take it into account
        for i, suggestions in enumerate(pipelines_suggestions):
            pipelines_suggestions[i] = suggestions[::-1]  # so we can pop from it later
            if not suggestions:
                probabilities[i] = 0.0
                empty_pipelines += 1

        name2suggestion: Dict[str, GeneratedName] = dict()

        # sampling itself
        while empty_pipelines < len(pipelines_suggestions) - 1 and len(name2suggestion) < max_suggestions:

            # if there is just enough space left for all the left available suggestions we simply turn on the specified
            # flag, which will skip every sampled suggestion, which is not available
            if max_suggestions - len(name2suggestion) == possible_available_count - available_used:
                sampling_only_available = True

            # otherwise we randomize pipeline from which to get the next suggestion
            probabilities = self._normalize_weights(probabilities)
            idx = choice(probabilities)

            # until we get a unique (not met yet) suggestion we pop suggestions from the chosen pipeline
            while pipelines_suggestions[idx]:
                suggestion = pipelines_suggestions[idx].pop()
                name = str(suggestion)
                existing_suggestion = name2suggestion.get(name, None)
                if existing_suggestion is None:
                    # if the flag is not set, then enter normally, else the suggestion must be available
                    if not sampling_only_available or suggestion.status == Domains.AVAILABLE:
                        name2suggestion[name] = suggestion
                        if suggestion.status == Domains.AVAILABLE:
                            available_used += 1
                        break
                else:
                    existing_suggestion.add_strategies(suggestion.applied_strategies)

            # if the chosen pipeline is emptied, then we update the corresponding variables and set probability to zero
            if not pipelines_suggestions[idx]:
                probabilities[idx] = 0.0
                empty_pipelines += 1
            else:
                probabilities[idx] /= 2

        # if only one non-empty pipeline is left and we still need suggestions (max_suggestions predicate is not met),
        # then we can simply take all the rest suggestions from it without sampling
        if empty_pipelines == len(pipelines_suggestions) - 1 and len(name2suggestion) < max_suggestions:
            # getting the index of the pipeline by checking which of them still has suggestions not popped
            # (others' lengths must be equal to 0)
            idx = np.argmax(list(map(len, pipelines_suggestions)))
            last_pipeline_suggestions = pipelines_suggestions[idx][::-1]  # it has been reversed before, so we undo it

            # for each suggestion we add it to the `name2suggestion` or aggregate if it has been met before
            for i, suggestion in enumerate(last_pipeline_suggestions):
                # if there is just enough space left for all the left available suggestions,
                # then we simply append them at the end
                if max_suggestions - len(name2suggestion) == possible_available_count - available_used:
                    name2suggestion = extend_and_aggregate(
                        name2suggestion,
                        [s for s in last_pipeline_suggestions[i:] if s.status == Domains.AVAILABLE],
                        max_suggestions
                    )
                    break

                # otherwise we simply add all the needed suggestions one by one
                name = str(suggestion)
                existing_suggestion = name2suggestion.get(name, None)
                if existing_suggestion is None:
                    name2suggestion[name] = suggestion
                    if suggestion.status == Domains.AVAILABLE:
                        available_used += 1
                else:
                    existing_suggestion.add_strategies(suggestion.applied_strategies)

                # if max_suggestion predicate is met, we interrupt the iteration
                if len(name2suggestion) >= max_suggestions:
                    break

        suggestions = list(name2suggestion.values())
        return suggestions
