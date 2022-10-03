import logging
from itertools import zip_longest, chain
from typing import List, Dict, Tuple

from omegaconf import DictConfig

from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.sorting import CountSorter, RoundRobinSorter, LengthSorter, WeightedSamplingSorter
from generator.sorting.sorter import Sorter
from generator.utils import aggregate_duplicates

logger = logging.getLogger('generator')


class Result:
    def __init__(self, config: DictConfig):
        self.domains = Domains(config)
        self.suggestions: List[List[GeneratedName]] = []

    def add_pipeline_suggestions(self, pipeline_suggestions: List[GeneratedName]):
        self.suggestions.append(pipeline_suggestions)

    def assign_categories(self) -> None:
        for pipeline_suggestions in self.suggestions:
            advertised, remaining_suggestions = self.domains.get_advertised(pipeline_suggestions)
            secondary, remaining_suggestions = self.domains.get_secondary(remaining_suggestions)
            primary, registered = self.domains.get_primary(remaining_suggestions)

            for category, suggestions in zip(['advertised', 'secondary', 'primary', 'registered'],
                                             [advertised, secondary, primary, registered]):

                for suggestion in suggestions:
                    suggestion.category = category

    def unique_suggestions(self) -> int:
        return len(set([
            str(suggestion)
            for pipeline_suggestions in self.suggestions
            for suggestion in pipeline_suggestions
        ]))


class Generator:
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            self.pipelines.append(Pipeline(definition, self.config))

        self.random_pipeline = Pipeline(self.config.random_pipeline, self.config)

        self.init_objects()

    def init_objects(self):
        Domains(self.config)

    def get_sorter(self, sorter: str) -> Sorter:
        match sorter:
            case 'count':
                return CountSorter(self.config)
            case 'round-robin':
                return RoundRobinSorter(self.config)
            case 'length':
                return LengthSorter(self.config)
            case 'weighted-sampling':
                return WeightedSamplingSorter(self.config)
            case _:
                raise ValueError(f'{sorter} is unavailable')

    def generate_names(
        self,
        name: str,
        sorter: str = 'weighted-sampling',
        min_suggestions: int = None,
        max_suggestions: int = None,
        min_primary_fraction: float = 0.1
    ) -> List[GeneratedName]:

        min_suggestions = min_suggestions or self.config.app.suggestions
        max_suggestions = max_suggestions or self.config.app.suggestions

        sorter = self.get_sorter(sorter)
        result = Result(self.config)

        for pipeline in self.pipelines:
            pipeline_suggestions = pipeline.apply(name)
            logger.debug(f'Pipeline suggestions: {pipeline_suggestions[:10]}')
            result.add_pipeline_suggestions(pipeline_suggestions)

        if result.unique_suggestions() < min_suggestions:
            # generate using random pipeline
            logger.debug('Generate random')
            random_suggestions = self.random_pipeline.apply(name)
            result.add_pipeline_suggestions(random_suggestions)

        result.assign_categories()
        suggestions = sorter.sort(result.suggestions, min_suggestions, max_suggestions, min_primary_fraction)

        return suggestions[:max_suggestions]
