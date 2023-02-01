import random
from copy import copy

from omegaconf import DictConfig

from generator.sorting.sorter import Sorter


class WeightedSorter(Sorter):
    #TODO better sorter: shuffle pipelines according to weights, return pipelines in that order, then sample with weights
    def __init__(self, config: DictConfig, pipelines: list, weights: dict):
        super().__init__(config)
        # self.pipelines = copy(pipelines)
        self.weights = weights

        for pipeline in pipelines:
            if self.weights[pipeline] <= 0:
                del self.weights[pipeline]

    def __iter__(self):
        return self

    def __next__(self):
        if self.weights:
            pipeline = random.choices(list(self.weights.keys()), weights=list(self.weights.values()))[0]  # TODO: optimize?
            return pipeline
        raise StopIteration

    def pipeline_used(self, sampled_pipeline):
        del self.weights[sampled_pipeline]
