import random, logging, math
from typing import List, Tuple, Dict, Collection

import numpy as np
import numpy.typing as npt
from omegaconf import DictConfig

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
            generators_per_pipeline[definition.name] = tuple(definition.generators)

        return generators_per_pipeline

    def _get_weights(self, pipeline_names: List[str]) -> npt.NDArray[np.float32]:
        return np.array([self.pipeline_weights.get(name, 0) for name in pipeline_names], dtype=np.float32)

    def _normalize_weights(self, weights: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        return weights / np.sum(weights)

    def sort(self,
             pipelines_suggestions: List[List[GeneratedName]],
             min_suggestions: int = None,
             max_suggestions: int = None) -> List[GeneratedName]:

        min_suggestions = min_suggestions or self.config.app.suggestions
        max_suggestions = max_suggestions or self.config.app.suggestions

        needed_primary_count = int(math.ceil(self.config.app.min_primary_fraction * min_suggestions))
        all_primary_count = len({
            str(suggestion)
            for pipeline_suggestions in pipelines_suggestions
            for suggestion in pipeline_suggestions
            if suggestion.category == 'primary'
        })

        pipeline_names = [
            suggestions[0].pipeline_name if suggestions else None
            for suggestions in pipelines_suggestions
        ]
        pipeline_weights = self._get_weights(pipeline_names)
        empty_pipelines = 0

        for i, suggestions in enumerate(pipelines_suggestions):
            pipelines_suggestions[i] = suggestions[::-1]  # so we can pop from it later
            if not suggestions:
                pipeline_weights[i] = 0.0
                empty_pipelines += 1

        name2suggestion: Dict[str, GeneratedName] = dict()
        primary_used = 0

        probabilities = pipeline_weights
        while empty_pipelines < len(pipelines_suggestions) - 1 and len(name2suggestion) < max_suggestions:
            probabilities = self._normalize_weights(probabilities)
            idx = choice(probabilities)

            while pipelines_suggestions[idx]:
                suggestion = pipelines_suggestions[idx].pop()
                name = str(suggestion)
                if name not in name2suggestion:
                    name2suggestion[name] = suggestion
                    if suggestion.category == 'primary':
                        primary_used += 1
                    break

                name2suggestion[name].add_strategies(suggestion.applied_strategies)

            if not pipelines_suggestions[idx]:
                probabilities[idx] = 0.0
                empty_pipelines += 1
            else:
                probabilities[idx] /= 2

            if max_suggestions - len(name2suggestion) == min(all_primary_count, needed_primary_count) - primary_used:
                name2suggestion = extend_and_aggregate(
                    name2suggestion,
                    [
                        suggestion
                        for pipeline_suggestions in pipelines_suggestions
                        for suggestion in pipeline_suggestions[::-1]
                        if suggestion.category == 'primary'
                    ]
                )
                break

        # FIXME what if empty_pipelines is not actualized and max_suggestions is not met yet
        if empty_pipelines == len(pipelines_suggestions) - 1 and len(name2suggestion) < max_suggestions:
            idx = np.argmax(list(map(len, pipelines_suggestions)))
            last_pipeline_suggestions = pipelines_suggestions[idx][::-1]

            for i, suggestion in enumerate(last_pipeline_suggestions):
                name = str(suggestion)
                if name in name2suggestion:
                    name2suggestion[name].add_strategies(suggestion.applied_strategies)
                else:
                    name2suggestion[name] = suggestion

                if max_suggestions - len(name2suggestion) == min(all_primary_count,needed_primary_count) - primary_used:
                    name2suggestion = extend_and_aggregate(
                        name2suggestion,
                        [s for s in last_pipeline_suggestions[i:] if s.category == 'primary']
                    )
                    break

                if len(name2suggestion) >= max_suggestions:
                    break

        suggestions = list(name2suggestion.values())
        return suggestions
