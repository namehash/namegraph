from omegaconf import DictConfig
import numpy as np

from generator.pipeline import Pipeline
from generator.sampling.sampler import Sampler
from generator.thread_utils import get_random_rng, get_numpy_rng


class WeightedSorter(Sampler):
    """
    Return a random pipeline with replacements according to the relative weights.
    """

    def __init__(self, config: DictConfig, pipelines: list[Pipeline], weights: dict[Pipeline, float]):
        super().__init__(config, pipelines, weights)
        self.weights = weights

        for pipeline in pipelines:
            if self.weights[pipeline] <= 0:
                del self.weights[pipeline]

    def __next__(self):
        if self.weights:
            pipeline = get_random_rng().choices(
                list(self.weights.keys()),
                weights=list(self.weights.values())
            )[0]  # TODO: optimize?
            return pipeline
        raise StopIteration

    def pipeline_used(self, sampled_pipeline):
        del self.weights[sampled_pipeline]


class WeightedSorterWithOrder(Sampler):
    """
    Firstly, shuffle pipelines according to the relative weights and returns in this order.
    Then return a random pipeline with replacements according to the relative weights.
    """

    def __init__(self, config: DictConfig, pipelines: list[Pipeline], weights: dict[Pipeline, float]):
        super().__init__(config, pipelines, weights)
        self.weights = weights

        for pipeline in pipelines:
            if self.weights[pipeline] <= 0:
                del self.weights[pipeline]

        if self.weights:
            normalized_weights = np.array(list(self.weights.values()))
            normalized_weights = normalized_weights / np.sum(normalized_weights)
            self.first_pass = get_numpy_rng().choice(list(self.weights.keys()), len(self.weights),
                                                     p=normalized_weights, replace=False).tolist()
        else:
            self.first_pass = []

    def __next__(self):
        if self.first_pass:
            return self.first_pass.pop(0)
        if self.weights:
            pipeline = get_random_rng().choices(list(self.weights.keys()), weights=list(self.weights.values()))[
                0]  # TODO: optimize?
            return pipeline
        raise StopIteration

    def pipeline_used(self, sampled_pipeline):
        del self.weights[sampled_pipeline]
