import random
from itertools import zip_longest, chain
from typing import List, Dict, Tuple

from generator.domains import Domains
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

        self.domains = Domains(config)

    def generate_names(self, name: str, count: int) -> Dict[str, List[str]]:
        suggestions = []

        for pipeline in self.pipelines:
            suggestions.append(pipeline.apply(name))

        combined_suggestions = list(by_one_iterator(suggestions))
        # TODO uniq
        advertised, remaining_suggestions = self.get_advertised(combined_suggestions)
        secondary, remaining_suggestions = self.get_secondary(remaining_suggestions)
        random_names = self.get_random(remaining_suggestions)

        results = {'advertised': advertised, 'secondary': secondary, 'primary': remaining_suggestions[:count],
                   'random': random_names}
        return results

    def get_advertised(self, suggestions: List[str]) -> Tuple[List[str], List[str]]:
        advertised = {}
        remaining_suggestions = []
        for suggestion in suggestions:
            if suggestion in self.domains.advertised:
                advertised[suggestion] = self.domains.advertised[suggestion]
            else:
                remaining_suggestions.append(suggestion)
        return [name_price[0] for name_price in
                sorted(advertised.items(), key=lambda name_price: name_price[1], reverse=True)], remaining_suggestions

    def get_secondary(self, suggestions: List[str]) -> Tuple[List[str], List[str]]:
        secondary = {}
        remaining_suggestions = []
        for suggestion in suggestions:
            if suggestion in self.domains.secondary_market:
                secondary[suggestion] = self.domains.secondary_market[suggestion]
            else:
                remaining_suggestions.append(suggestion)
        return [name_price[0] for name_price in secondary.items()], remaining_suggestions

    def get_random(self, remaining_suggestions):
        result = list(self.domains.internet - set(remaining_suggestions))
        random.shuffle(result)
        return result[:self.config.app.suggestions]
