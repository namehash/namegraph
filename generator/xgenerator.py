import logging
from itertools import zip_longest, chain
from typing import List, Dict, Tuple

from omegaconf import DictConfig

from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.sorting import CountSorter, RoundRobinSorter, LengthSorter
from generator.sorting.sorter import Sorter
from generator.utils import aggregate_duplicates

logger = logging.getLogger('generator')


class Result:
    def __init__(self, config: DictConfig):
        self.advertised: List[List[GeneratedName]] = []
        self.secondary: List[List[GeneratedName]] = []
        self.primary: List[List[GeneratedName]] = []

        self.domains = Domains(config)
        self.suggestions: List[List[GeneratedName]] = []

    def add_pipeline_suggestions(self, pipeline_suggestions: List[GeneratedName]):
        self.suggestions.append(pipeline_suggestions)

    def split(self) -> None:
        for pipeline_suggestions in self.suggestions:
            advertised, remaining_suggestions = self.domains.get_advertised(pipeline_suggestions)
            secondary, remaining_suggestions = self.domains.get_secondary(remaining_suggestions)
            primary = self.domains.get_primary(remaining_suggestions)
            self.advertised.append(advertised)
            self.secondary.append(secondary)
            self.primary.append(primary)

    def combine(self, sorter: Sorter) -> Tuple[List[GeneratedName], List[GeneratedName], List[GeneratedName]]:
        advertised = sorter.sort(self.advertised)
        secondary = sorter.sort(self.secondary)
        primary = sorter.sort(self.primary)

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

    # TODO should we do this like in pipeline.py? using globals()
    def get_sorter(self, sorter: str) -> Sorter:
        match sorter:
            case 'count':
                return CountSorter(self.config)
            case 'round-robin':
                return RoundRobinSorter(self.config)
            case 'length':
                return LengthSorter(self.config)
            case _:
                # TODO do we need this? is it better to silently select the default sorter, instead of informing the
                # TODO client about the wrong sorter name or smth?
                raise ValueError(f'{sorter} is not available')

    def generate_names(
        self,
        name: str,
        sorter: str = 'round-robin',
        min_suggestions: int = None,
        max_suggestions: int = None
    ) -> Dict[str, List[GeneratedName]]:

        if min_suggestions is None:
            min_suggestions = self.config.app.suggestions
        if max_suggestions is None:
            max_suggestions = self.config.app.suggestions

        sorter = self.get_sorter(sorter)
        result = Result(self.config)

        for pipeline in self.pipelines:
            pipeline_suggestions = pipeline.apply(name)
            logger.debug(f'Pipeline suggestions: {pipeline_suggestions[:10]}')
            result.add_pipeline_suggestions(pipeline_suggestions)

        result.split()
        advertised, secondary, primary = result.combine(sorter)

        if len(primary) < min_suggestions:
            # generate using random pipeline
            logger.debug('Generate random')
            random_suggestions = self.random_pipeline.apply(name)
            result_random = Result(self.config)
            result_random.add_pipeline_suggestions(random_suggestions)
            result_random.split()
            _, _, random_names = result_random.combine(sorter)
            # TODO do we need to truncate the random suggestions before sorting?
            primary = sorter.sort([aggregate_duplicates(primary + random_names)[:min_suggestions]])

        results = {'advertised': advertised[:max_suggestions],
                   'secondary': secondary[:max_suggestions],
                   'primary': primary[:max_suggestions]}
        return results
