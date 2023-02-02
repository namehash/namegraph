import random

import numpy.random
from omegaconf import DictConfig

from generator.pipeline import Pipeline
from generator.sampling.sampler import Sampler


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
            print(self.weights)
            print(list(self.weights.keys()), list(self.weights.values()))
            pipeline = random.choices(list(self.weights.keys()), weights=list(self.weights.values()))[
                0]  # TODO: optimize?
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

        normalized_weights = numpy.array(list(self.weights.values()))
        normalized_weights = normalized_weights / numpy.sum(normalized_weights)

        self.first_pass = numpy.random.choice(list(self.weights.keys()), len(self.weights),
                                              p=normalized_weights, replace=False).tolist()

    def __next__(self):
        if self.first_pass:
            return self.first_pass.pop(0)
        if self.weights:
            print(self.weights)
            print(list(self.weights.keys()), list(self.weights.values()))
            pipeline = random.choices(list(self.weights.keys()), weights=list(self.weights.values()))[
                0]  # TODO: optimize?
            return pipeline
        raise StopIteration

    def pipeline_used(self, sampled_pipeline):
        del self.weights[sampled_pipeline]
