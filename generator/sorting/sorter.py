from typing import List

from generator.generated_name import GeneratedName


class Sorter:
    def __init__(self, config):
        self.config = config

    def sort(self, pipelines_suggestions: List[List[GeneratedName]]) -> List[GeneratedName]:
        raise NotImplementedError
