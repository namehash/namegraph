import logging
from itertools import zip_longest, chain
from typing import List, Dict, Tuple, Any

from omegaconf import DictConfig

from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.sorting import CountSorter, RoundRobinSorter, LengthSorter, WeightedSamplingSorter
from generator.sorting.sorter import Sorter

logger = logging.getLogger('generator')


class Result:
    def __init__(self, config: DictConfig):
        self.domains = Domains(config)
        self.suggestions: List[List[GeneratedName]] = []

    def add_pipeline_suggestions(self, pipeline_suggestions: List[GeneratedName]):
        self.suggestions.append(pipeline_suggestions)

    def assign_categories(self) -> None:
        for pipeline_suggestions in self.suggestions:
            # advertised, remaining_suggestions = self.domains.get_advertised(pipeline_suggestions)
            on_sale, remaining_suggestions = self.domains.get_on_sale(pipeline_suggestions)
            available, taken = self.domains.get_available(remaining_suggestions)

            for category, suggestions in zip(['on_sale', 'available', 'taken'],
                                             [on_sale, available, taken]):

                for suggestion in suggestions:
                    suggestion.category = category

    def unique_suggestions(self) -> int:
        return len(set([
            str(suggestion)
            for pipeline_suggestions in self.suggestions
            for suggestion in pipeline_suggestions
        ]))

    def available_suggestions(self) -> int:
        return len([
            suggestion
            for pipeline_suggestions in self.suggestions
            for suggestion in pipeline_suggestions
            if suggestion.category == 'available'
        ])


class Generator:
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            self.pipelines.append(Pipeline(definition, self.config))

        self.random_available_name_pipeline = Pipeline(self.config.random_available_name_pipeline, self.config)

        self.init_objects()

    def init_objects(self):
        self.domains = Domains(self.config)

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
            min_available_fraction: float = 0.1,
            params: dict[str, Any] = None
    ) -> list[GeneratedName]:

        min_suggestions = min_suggestions or self.config.app.suggestions
        max_suggestions = max_suggestions or self.config.app.suggestions

        sorter = self.get_sorter(sorter)
        result = Result(self.config)

        for pipeline in self.pipelines:
            pipeline_suggestions = pipeline.apply(name, params)
            logger.debug(f'Pipeline suggestions: {pipeline_suggestions[:10]}')
            result.add_pipeline_suggestions(pipeline_suggestions)

        result.assign_categories()

        required_available_suggestions = min_available_fraction * min_suggestions
        if result.unique_suggestions() < min_suggestions \
                or result.available_suggestions() < required_available_suggestions:
            logger.debug('Generate only available random')
            only_available_suggestions = self.random_available_name_pipeline.apply(name)
            result.add_pipeline_suggestions(only_available_suggestions)

        result.assign_categories()
        suggestions = sorter.sort(result.suggestions, min_suggestions, max_suggestions, min_available_fraction)

        return suggestions[:max_suggestions]
