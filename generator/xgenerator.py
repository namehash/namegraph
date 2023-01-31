import logging
import random
from itertools import zip_longest, chain
from typing import List, Dict, Tuple, Any

from omegaconf import DictConfig

from generator.do import Do
from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.sorting import CountSorter, RoundRobinSorter, LengthSorter, WeightedSamplingSorter
from generator.sorting.round_robin_sorter import RoundRobinSorter2
from generator.sorting.sorter import Sorter
from generator.the_name import TheName
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


class MetaSampler:
    def __init__(self, name: TheName, config, pipelines):
        self.name = name
        self.sorters = {}
        for type, interpretations in name.interpretations.items():
            for interpretation in interpretations:
                print(type, interpretation.tokenization, interpretation.in_type_probability, interpretation.features)
                # self.sorters[interpretation] = self.get_sorter(sorter)  # TODO weights
                self.sorters[interpretation] = RoundRobinSorter2(config, pipelines)  # TODO weights

        self.types_weights = {}
        self.interpretation_weights = {}
        for type, weight in self.name.types_probabilities.items():
            if weight > 0:
                self.types_weights[type] = weight
                self.interpretation_weights[type] = {}
                for interpretation in self.name.interpretations[type]:
                    self.interpretation_weights[type][interpretation] = interpretation.in_type_probability

    def sample(self) -> list[GeneratedName]:
        all_suggestions = []
        all_suggestions_str = set()
        while True:
            # losuj interpretację
            if not self.types_weights:
                break

            sampled_type = random.choices(list(self.types_weights.keys()),
                                          weights=list(self.types_weights.values()))[0]
            # print('Sampled type:', sampled_type, self.types_weights)
            sampled_interpretation = random.choices(list(self.interpretation_weights[sampled_type].keys()),
                                                    weights=list(self.interpretation_weights[sampled_type].values()))[0]
            # print('Sampled interpretation:', sampled_interpretation.tokenization,
            #       self.interpretation_weights[sampled_type])
            # losuj pipeline
            while True:
                try:

                    sampled_pipeline = next(self.sorters[sampled_interpretation])
                    # for sampled_pipeline in self.sorters[sampled_interpretation]:
                    # print('Sampled pipeline:', sampled_pipeline.definition.name)

                    # odpal pipeline
                    suggestions = sampled_pipeline.apply(self.name, sampled_interpretation)
                    # print('Length', len(suggestions))
                    added_suggestion = False
                    while True:
                        try:
                            suggestion = next(suggestions)
                            # wez kolejny jeśli nie spełnia wymagań: duplikat lub nonavailable
                            if str(suggestion) in all_suggestions_str:
                                continue
                            else:
                                # sprawdz status
                                # jesli ma byc dostpne a nie jest to continue
                                added_suggestion = True
                                all_suggestions.append(suggestion)
                                all_suggestions_str.add(str(suggestion))
                                break
                        except StopIteration:
                            # print('Empty pipeline', sampled_interpretation.tokenization, sampled_pipeline.definition.name)
                            # jesli pusty to oznacz pipeline jako zużyty dla tej interpretacji
                            self.sorters[sampled_interpretation].pipeline_used(sampled_pipeline)
                            # jesli wszystkie zuzyte to usun interpretacje z losowania
                            # MEtaSampler
                            break
                    if added_suggestion:
                        break
                except StopIteration:
                    # print('interpretacja skonczona')
                    # usun interpretację z losowania
                    del self.interpretation_weights[sampled_type][sampled_interpretation]
                    if not self.interpretation_weights[sampled_type]:
                        del self.interpretation_weights[sampled_type]
                        del self.types_weights[sampled_type]
                    break

        return all_suggestions


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
        self.do = Do(config)

        self.weights = {}
        for definition in self.config.pipelines:
            self.weights[definition.name] = definition.weights

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

        name = TheName(name, params)
        self.do.normalize(name)
        self.do.classify(name)

        for pipeline in self.pipelines:
            pipeline.clear_cache()

        print(name.types_probabilities)

        metasampler = MetaSampler(name, self.config, self.pipelines)
        # 2. utwórz sorter dla każdej interpretacji
        # for type, interpretations in name.interpretations.items():
        #     for interpretation in interpretations:
        #         print(type, interpretation.tokenization, interpretation.in_type_probability, interpretation.features)
        #         # interpretation.sorter = self.get_sorter(sorter)  # TODO weights
        #         interpretation.sorter = RoundRobinSorter2(self.config, self.pipelines)  # TODO weights

        all_suggestions = metasampler.sample()

        print('Generated suggestions', len(all_suggestions), len(set([str(x) for x in all_suggestions])))

        if len(all_suggestions) < min_suggestions:
            only_available_suggestions = self.random_available_name_pipeline.apply(name, None)
            all_suggestions.extend(only_available_suggestions)  # TODO dodawaj do osiągnięcia limitu
            print('Generated suggestions 2', len(all_suggestions), len(set([str(x) for x in all_suggestions])))
            all_suggestions=aggregate_duplicates(all_suggestions)

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
