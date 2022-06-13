import logging
import random
from itertools import zip_longest, chain
from typing import List, Dict, Tuple

from generator.domains import Domains
from generator.pipeline import Pipeline
from omegaconf import DictConfig

logger = logging.getLogger('generator')


def by_one_iterator(lists):
    return [x for x in chain(*zip_longest(*lists)) if x is not None]


def by_one_iterator_uniq(lists):
    used = set()

    iters = [iter(l) for l in lists]

    while True:
        all_empty = True
        for i in iters:
            while True:
                try:
                    x = next(i)
                    if x is not None and x not in used:
                        all_empty = False
                        used.add(x)
                        yield x
                        break
                except StopIteration:
                    break

        if all_empty: break


def uniq(l: List):
    used = set()
    return [x for x in l if x not in used and (used.add(x) or True)]


class Generator():
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            self.pipelines.append(Pipeline(definition, self.config))

        self.domains = Domains(config)

    def generate_names(self, name: str) -> Dict[str, List[str]]:
        count = self.config.app.suggestions
        suggestions = []

        for pipeline in self.pipelines:
            pipeline_suggestions = pipeline.apply(name)
            logger.debug(f'Pipeline suggestions: {pipeline_suggestions[:10]}')
            suggestions.append(pipeline_suggestions)

        combined_suggestions = list(by_one_iterator_uniq(suggestions))

        # combined_suggestions = uniq(combined_suggestions)

        advertised, remaining_suggestions = self.domains.get_advertised(combined_suggestions)
        secondary, remaining_suggestions = self.domains.get_secondary(remaining_suggestions)
        primary = self.domains.get_primary(remaining_suggestions)

        results = {'advertised': advertised[:count],
                   'secondary': secondary[:count],
                   'primary': primary[:count]}
        return results
