from typing import List, Tuple, Dict

import numpy as np
import numpy.typing as npt
from omegaconf import DictConfig

from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName
from generator.utils import softmax


class WeightedSamplingSorter(Sorter):
    def __init__(self, config: DictConfig):
        super().__init__(config)
        sorter_config = self.config.sorting.weighted_sampling

        self.use_softmax = sorter_config.use_softmax
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
        if self.use_softmax:
            return softmax(weights)

        return weights / np.sum(weights)

    def sort(self, pipelines_suggestions: List[List[GeneratedName]]) -> List[GeneratedName]:
        pipeline_names = [
            suggestions[0].pipeline_name if suggestions else None
            for suggestions in pipelines_suggestions
        ]
        pipeline_weights = self._get_weights(pipeline_names)
        empty_pipelines = 0

        for i, suggestions in enumerate(pipelines_suggestions):
            pipelines_suggestions[i] = suggestions[::-1]  # so we can pop from it later
            if not suggestions:
                pipeline_weights[i] = float('-inf') if self.use_softmax else 0.0
                empty_pipelines += 1

        pipeline_idxs = list(range(len(pipelines_suggestions)))
        name2suggestion: Dict[str, GeneratedName] = dict()

        while empty_pipelines < len(pipelines_suggestions) - 1:
            probabilities = self._normalize_weights(pipeline_weights)
            idx = np.random.choice(pipeline_idxs, p=probabilities)

            while pipelines_suggestions[idx]:
                suggestion = pipelines_suggestions[idx].pop()
                name = str(suggestion)
                if name not in name2suggestion:
                    name2suggestion[name] = suggestion
                    break

                name2suggestion[name].add_strategies(suggestion.applied_strategies)

            if not pipelines_suggestions[idx]:
                pipeline_weights[idx] = float('-inf') if self.use_softmax else 0.0
                empty_pipelines += 1
            else:
                pipeline_weights[idx] /= 2

            zero_replaced = np.where(np.isclose(pipeline_weights, 0.0, atol=1.0e-30), 1.0, pipeline_weights)
            if np.min(zero_replaced) < 1.0e-25:
                pipeline_weights *= 2

        if empty_pipelines == len(pipelines_suggestions) - 1:
            idx = np.argmax(map(len, pipelines_suggestions))

            for suggestion in pipelines_suggestions[idx][::-1]:
                name = str(suggestion)
                if name in name2suggestion:
                    name2suggestion[name].add_strategies(suggestion.applied_strategies)
                else:
                    name2suggestion[name] = suggestion

        suggestions = list(name2suggestion.values())
        return suggestions
