import logging
from typing import List, Any

import wordninja
from omegaconf import DictConfig

from generator.preprocessor import Preprocessor
from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.meta_sampler import MetaSampler
from generator.input_name import InputName
from generator.utils import aggregate_duplicates

logger = logging.getLogger('generator')


class Result:
    def __init__(self, config: DictConfig):
        self.domains = Domains(config)
        self.suggestions: List[List[GeneratedName]] = []

    def add_pipeline_suggestions(self, pipeline_suggestions: List[GeneratedName]):
        self.suggestions.append(pipeline_suggestions)

    def assign_statuses(self) -> None:
        for pipeline_suggestions in self.suggestions:
            for suggestion in pipeline_suggestions:
                suggestion.status = self.domains.get_name_status(str(suggestion))

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
            if suggestion.status == Domains.AVAILABLE
        ])


class Generator:
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            # logger.info('start ' + str(definition.name))
            self.pipelines.append(Pipeline(definition, self.config))
            # logger.info('end ' + str(definition.name))

        self.random_available_name_pipeline = Pipeline(self.config.random_available_name_pipeline, self.config)

        self.init_objects()
        self.preprocessor = Preprocessor(config)
        self.metasampler = MetaSampler(config, self.pipelines)

        # self.weights = {}
        # for definition in self.config.pipelines:
        #     self.weights[definition.name] = definition.weights

        # new grouped endpoint
        # 1. split pipelines into categories
        generator_to_category = {}
        for category, generator_names in self.config.generation.grouping_categories.items():
            for generator_name in generator_names:
                generator_to_category[generator_name] = category

        self.pipelines_grouped = {}
        for pipeline in self.pipelines:
            if pipeline.definition.generator in generator_to_category:
                category = generator_to_category[pipeline.definition.generator]
                if category not in self.pipelines_grouped:
                    self.pipelines_grouped[category] = []
                self.pipelines_grouped[category].append(pipeline)

        print(self.pipelines_grouped)

        # 2. Within each category: sample type and lang of interpretation, sample interpretaion with this type and lang. Sample pipeline (weights of pipelines depends on type and language. Do it in parallel?
        self.grouped_metasamplers = {}
        for category, pipelines in self.pipelines_grouped.items():
            self.grouped_metasamplers[category] = MetaSampler(config, pipelines)

        # 3. Sample `max number of suggestions per category`. How handle `min_available_fraction`?

    def init_objects(self):
        self.domains = Domains(self.config)
        wordninja.DEFAULT_LANGUAGE_MODEL = wordninja.LanguageModel(self.config.tokenization.wordninja_dictionary)

    def generate_names(
            self,
            name: str,
            sorter: str = 'weighted-sampling',
            min_suggestions: int = None,
            max_suggestions: int = None,
            min_available_fraction: float = 0.1,
            params: dict[str, Any] = None
    ) -> list[GeneratedName]:
        params = params or {}

        min_suggestions = min_suggestions or self.config.app.suggestions
        max_suggestions = max_suggestions or self.config.app.suggestions
        min_available_fraction = min_available_fraction or self.config.app.min_available_fraction

        params['min_suggestions'] = min_suggestions
        params['max_suggestions'] = max_suggestions
        params['min_available_fraction'] = min_available_fraction

        name = InputName(name, params)
        logger.info('Start normalize')
        self.preprocessor.normalize(name)
        logger.info('Start classify')
        self.preprocessor.classify(name)
        logger.info('End preprocessing')

        logger.info(str(name.types_probabilities))

        logger.info('Start sampling')
        all_suggestions = self.metasampler.sample(name, sorter, min_suggestions=name.params['min_suggestions'],
                                                  max_suggestions=name.params['max_suggestions'],
                                                  min_available_fraction=name.params['min_available_fraction'])

        logger.info(f'Generated suggestions: {len(all_suggestions)}')

        if len(all_suggestions) < min_suggestions:
            only_available_suggestions = self.random_available_name_pipeline.apply(name, None)
            all_suggestions.extend(only_available_suggestions)  # TODO dodawaj do osiągnięcia limitu
            logger.info(f'Generated suggestions after random: {len(all_suggestions)}')
            all_suggestions = aggregate_duplicates(all_suggestions)

        return all_suggestions[:max_suggestions]

    def generate_grouped_names(
            self,
            name: str,
            max_related_collections: int = 5,
            max_names_per_related_collection: int = 5,
            max_recursive_related_collections: int = 5,
            other_categories_params: dict[str, Any] = None,
            min_total_suggestions: float = 50,
            params: dict[str, Any] = None
    ) -> list[GeneratedName]:
        params = params or {}
        other_categories_params = other_categories_params or {}

        params['max_related_collections'] = max_related_collections
        params['max_names_per_related_collection'] = max_names_per_related_collection
        params['max_recursive_related_collections'] = max_recursive_related_collections
        params['other_categories_params'] = other_categories_params
        params['min_total_suggestions'] = min_total_suggestions
        params['max_suggestions'] = 200 # TODO used to limit generators
        min_available_fraction = 0.0

        name = InputName(name, params)
        logger.info('Start normalize')
        self.preprocessor.normalize(name)
        logger.info('Start classify')
        self.preprocessor.classify(name)
        logger.info('End preprocessing')

        logger.info(str(name.types_probabilities))

        logger.info('Start sampling')
 
        all_suggestions = []
        for category, meta_sampler in self.grouped_metasamplers.items():
            try:
                min_suggestions = other_categories_params[category].min_suggestions
                max_suggestions = other_categories_params[category].max_suggestions
            except KeyError:
                min_suggestions = 0
                max_suggestions = 30
            
            suggestions = meta_sampler.sample(name, 'weighted-sampling',
                                                  min_suggestions=min_suggestions,
                                                  max_suggestions=max_suggestions,
                                                  min_available_fraction=min_available_fraction)
            logger.info(f'Generated suggestions: {len(suggestions)}')
            all_suggestions.extend(suggestions)

        #agregate duplicates
        all_suggestions = aggregate_duplicates(all_suggestions)

            # all_suggestions = self.metasampler.sample(name, 'weighted-sampling',
            #                                           min_suggestions=min_suggestions,
            #                                           max_suggestions=max_suggestions,
            #                                           min_available_fraction=min_available_fraction)

        logger.info(f'Generated suggestions: {len(all_suggestions)}')

        if len(all_suggestions) < min_total_suggestions:
            only_available_suggestions = self.random_available_name_pipeline.apply(name, None)
            all_suggestions.extend(only_available_suggestions)  # TODO dodawaj do osiągnięcia limitu
            logger.info(f'Generated suggestions after random: {len(all_suggestions)}')
            all_suggestions = aggregate_duplicates(all_suggestions)

        return all_suggestions

    def clear_cache(self) -> None:
        for pipeline in self.pipelines:
            pipeline.clear_cache()
        self.random_available_name_pipeline.clear_cache()
