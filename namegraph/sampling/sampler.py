from omegaconf import DictConfig

from namegraph.pipeline import Pipeline


class Sampler:
    """
    Return next pipeline to be sampled from.
    """

    def __init__(self, config: DictConfig, pipelines: list[Pipeline], weights: dict[Pipeline, float]):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError

    def pipeline_used(self, sampled_pipeline):
        raise NotImplementedError
