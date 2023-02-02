import logging
from typing import List, Any

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

    def assign_categories(self) -> None:
        for pipeline_suggestions in self.suggestions:
            for suggestion in pipeline_suggestions:
                suggestion.category = self.domains.get_name_status(str(suggestion))

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
            if suggestion.category == Domains.AVAILABLE
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

        self.weights = {}
        for definition in self.config.pipelines:
            self.weights[definition.name] = definition.weights

    def init_objects(self):
        self.domains = Domains(self.config)

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
        all_suggestions = self.metasampler.sample(name, sorter)

        logger.info(f'Generated suggestions: {len(all_suggestions)}')

        if len(all_suggestions) < min_suggestions:
            only_available_suggestions = self.random_available_name_pipeline.apply(name, None)
            all_suggestions.extend(only_available_suggestions)  # TODO dodawaj do osiągnięcia limitu
            logger.info(f'Generated suggestions after random: {len(all_suggestions)}')
            all_suggestions = aggregate_duplicates(all_suggestions)

        # all_suggestions = []
        # for i in range(100):
        #     # losuj interpretację
        #     sampled_type = random.choices(list(name.types_probabilities.keys()),
        #                                   weights=list(name.types_probabilities.values()))[0]
        #     print('Sampled type:', sampled_type)
        #     sampled_interpretation = random.choices(name.interpretations[sampled_type],
        #                                             weights=[i.in_type_probability for i in
        #                                                      name.interpretations[sampled_type]])[0]
        #     print('Sampled interpretation:', sampled_interpretation.tokenization)
        #     # losuj pipeline
        #     for sampled_pipeline in sampled_interpretation.sorter.next_pipeline():
        #         print('Sampled pipeline:', sampled_pipeline.definition.name)
        #         break
        # 
        #     # odpal pipeline
        #     suggestions = sampled_pipeline.apply(name, sampled_interpretation)
        #     try:
        #         suggestion = next(suggestions)
        #     except:
        #         print('Empty pipeline')
        #         # jesli pusty to oznacz pipeline jako zużyty dla tej interpretacji
        #         # jesli wszystkie zuzyte to usun interpretacje z losowania
        #         # MEtaSampler
        #         continue
        #     all_suggestions.append(suggestion)

        # sorter = self.get_sorter(sorter)
        # result = Result(self.config)
        # 
        # for pipeline in self.pipelines:
        #     pipeline_suggestions = pipeline.apply(name, params)
        #     logger.debug(f'Pipeline suggestions: {pipeline_suggestions[:10]}')
        #     result.add_pipeline_suggestions(pipeline_suggestions)

        # result.assign_categories()

        # required_available_suggestions = min_available_fraction * min_suggestions
        # if result.unique_suggestions() < min_suggestions \
        #         or result.available_suggestions() < required_available_suggestions:
        #     logger.debug('Generate only available random')
        #     only_available_suggestions = self.random_available_name_pipeline.apply(name)
        #     result.add_pipeline_suggestions(only_available_suggestions)
        # 
        # result.assign_categories()
        # suggestions = sorter.sort(result.suggestions, min_suggestions, max_suggestions, min_available_fraction)
        # 
        return all_suggestions[:max_suggestions]

    def clear_cache(self) -> None:
        for pipeline in self.pipelines:
            pipeline.clear_cache()
        self.random_available_name_pipeline.clear_cache()
