from copy import copy

from omegaconf import DictConfig

from namegraph.pipeline import Pipeline
from namegraph.sampling.sampler import Sampler


class RoundRobinSampler(Sampler):
    """
    Return next pipeline using round-robin.
    """
    def __init__(self, config: DictConfig, pipelines: list[Pipeline], weights: dict[Pipeline, float]):
        super().__init__(config, pipelines, weights)
        self.used_pipelines = set()
        self.pipelines = copy(pipelines)
        self.index = 0

    def __next__(self):
        # print('Robin', self.index , len(self.pipelines), self, [p.definition.name for p in self.pipelines])
        if self.index < len(self.pipelines):
            pipeline = self.pipelines[self.index]
            self.index = (self.index + 1) % len(self.pipelines)
            return pipeline
        raise StopIteration

    def pipeline_used(self, sampled_pipeline):
        self.pipelines.remove(sampled_pipeline)
        if len(self.pipelines):
            self.index = self.index % len(self.pipelines)
