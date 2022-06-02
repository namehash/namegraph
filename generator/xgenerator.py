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

        # self.domains = set()
        # self.tokenizer = TwoWordWordNetTokenizer()
        # self.strategies = [WordNetSynonyms()]

    # def read_domains(self, path):
    #     with open(path) as domains_file:
    #         for line in domains_file:
    #             self.domains.add(line.strip()[:-4])
    #     return self.domains

    def generate_names(self, name: str, count: int) -> List[str]:
        suggestions = []

        for pipeline in self.pipelines:
            suggestions.extend(pipeline.apply(name))

        # suggestions = [str(name) for name in suggestions]

        # suggestions = uniq(suggestions)

        return suggestions[:count]
