from itertools import zip_longest, chain
from typing import List

from generator.pipeline import Pipeline
from omegaconf import DictConfig


def by_one_iterator(lists):
    return [x for x in chain(*zip_longest(*lists)) if x is not None]


class Generator():
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            self.pipelines.append(Pipeline(definition, self.config))

    def generate_names(self, name: str, count: int) -> List[str]:
        suggestions = []

        for pipeline in self.pipelines:
            suggestions.append(pipeline.apply(name))

        combined_suggestions = list(by_one_iterator(suggestions))
        # TODO uniq

        return combined_suggestions[:count]
