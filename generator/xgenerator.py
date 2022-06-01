from typing import List

from generator.pipeline import Pipeline
from generator.utils import uniq
from omegaconf import DictConfig


class Generator():
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.app.pipelines:
            self.pipelines.append(Pipeline(definition, self.config))

    def generate_names(self, name: str, count: int) -> List[str]:
        suggestions = []

        for pipeline in self.pipelines:
            suggestions.extend(pipeline.apply(name))

        return suggestions[:count]
