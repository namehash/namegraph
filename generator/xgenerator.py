import logging
from itertools import zip_longest, chain
from typing import List, Dict

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


class Result:
    def __init__(self, config: DictConfig):
        self.advertised = []
        self.secondary = []
        self.primary = []

        self.domains = Domains(config)
        self.suggestions = []

    def add_pipeline_suggestions(self, pipeline_suggestions):
        self.suggestions.append(pipeline_suggestions)

    def split(self):
        for pipeline_suggestions in self.suggestions:
            advertised, remaining_suggestions = self.domains.get_advertised(pipeline_suggestions)
            secondary, remaining_suggestions = self.domains.get_secondary(remaining_suggestions)
            primary = self.domains.get_primary(remaining_suggestions)
            self.advertised.append(advertised)
            self.secondary.append(secondary)
            self.primary.append(primary)

    def combine(self):
        advertised = list(by_one_iterator_uniq(self.advertised))
        secondary = list(by_one_iterator_uniq(self.secondary))
        primary = list(by_one_iterator_uniq(self.primary))
        return advertised, secondary, primary


class Generator():
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            self.pipelines.append(Pipeline(definition, self.config))

        self.random_pipeline = Pipeline(self.config.random_pipeline, self.config)

        self.init_objects()

    def init_objects(self):
        Domains(self.config)

    def generate_names(self, name: str) -> Dict[str, List[str]]:
        count = self.config.app.suggestions
        result = Result(self.config)

        for pipeline in self.pipelines:
            pipeline_suggestions = pipeline.apply(name)
            logger.debug(f'Pipeline suggestions: {pipeline_suggestions[:10]}')
            result.add_pipeline_suggestions(pipeline_suggestions)

        result.split()
        advertised, secondary, primary = result.combine()

        if len(primary) < count:
            # generate using random pipeline
            logger.debug('Generate random')
            random_suggestions = self.random_pipeline.apply(name)
            result_random = Result(self.config)
            result_random.add_pipeline_suggestions(random_suggestions)
            result_random.split()
            _, _, random_names = result_random.combine()
            primary += random_names

        results = {'advertised': advertised[:count],
                   'secondary': secondary[:count],
                   'primary': primary[:count]}
        return results
