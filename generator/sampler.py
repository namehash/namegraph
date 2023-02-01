import logging
import random

from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.sorting.round_robin_sorter import RoundRobinSorter2
from generator.the_name import TheName

logger = logging.getLogger('generator')


class MetaSampler:
    def __init__(self, name: TheName, config, pipelines):
        self.domains = Domains(config)
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
        logger.info('Start sampling')
        min_suggestions = self.name.params['min_suggestions']
        max_suggestions = self.name.params['max_suggestions']
        min_available_fraction = self.name.params['min_available_fraction']
        min_available = int(min_suggestions * min_available_fraction)

        count_available = 0

        all_suggestions = []
        all_suggestions_str = set()
        while True:
            if len(all_suggestions) >= max_suggestions: break
            # losuj interpretację
            if not self.types_weights:
                break

            sampled_type = random.choices(list(self.types_weights.keys()),
                                          weights=list(self.types_weights.values()))[0]
            # print('Sampled type:', sampled_type, self.types_weights)
            # print(list(self.interpretation_weights[sampled_type].items()))
            # print(list([(x.tokenization) for x in self.interpretation_weights[sampled_type].keys()]))
            sampled_interpretation = random.choices(list(self.interpretation_weights[sampled_type].keys()),
                                                    weights=list(self.interpretation_weights[sampled_type].values()))[0]
            # print('Sampled interpretation:', sampled_interpretation.tokenization,
            #       self.interpretation_weights[sampled_type])
            # losuj pipeline
            while True:
                try:
                    if len(all_suggestions) >= max_suggestions: break

                    sampled_pipeline = next(self.sorters[sampled_interpretation])
                    # for sampled_pipeline in self.sorters[sampled_interpretation]:
                    # print('Sampled pipeline:', sampled_pipeline.definition.name)

                    # odpal pipeline
                    suggestions = sampled_pipeline.apply(self.name, sampled_interpretation)
                    # print('Length', len(suggestions))
                    added_suggestion = False
                    while True:
                        try:
                            if len(all_suggestions) >= max_suggestions: break

                            suggestion = next(suggestions)
                            # wez kolejny jeśli nie spełnia wymagań: duplikat lub nonavailable
                            if str(suggestion) in all_suggestions_str:
                                logger.info('Duplicated suggestion')
                                continue
                            else:
                                # sprawdz status
                                suggestion.category = self.domains.get_name_status(str(suggestion))

                                # jesli ma byc dostpne a nie jest to continue
                                if suggestion.category == Domains.AVAILABLE or count_available + max_suggestions - len(
                                        all_suggestions) > min_available:
                                    added_suggestion = True
                                    if suggestion.category == Domains.AVAILABLE:
                                        count_available += 1
                                    all_suggestions.append(suggestion)
                                    all_suggestions_str.add(str(suggestion))
                                    break
                                else:
                                    logger.info('Skipping nonavailable suggestion')
                                    # print('Skip non vailable', min_available, count_available, max_suggestions - len(
                                    #     all_suggestions))
                                    continue
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
