from typing import List
import logging, math

from omegaconf import DictConfig

from generator.domains import Domains
from generator.generated_name import GeneratedName


logger = logging.getLogger('generator')


class Sorter:
    def __init__(self, config: DictConfig):
        self.config = config
        self.default_suggestions_count = self.config.app.suggestions
        self.default_min_available_fraction = self.config.app.min_available_fraction

    def maximize_available_fraction(self,
                                    suggestions: List[GeneratedName],
                                    needed_available_count: int,
                                    max_suggestions: int,
                                    all_available_count: int = None) -> List[GeneratedName]:

        if all_available_count is None:
            all_available_count = len([str(s) for s in suggestions if s.status == Domains.AVAILABLE])

        needed_available_count = min(needed_available_count, all_available_count)
        
        available_used = 0
        for i, s in enumerate(suggestions):
            # if there is just enough space left for all the left available suggestions we simply append them at the end
            if max_suggestions - i <= needed_available_count - available_used:
                rest_available = [s for s in suggestions[i:] if s.status == 'available']
                assert len(rest_available) >= needed_available_count - available_used

                return suggestions[:i] + rest_available

            if s.status == 'available':
                available_used += 1

        logger.warning('weird parameters used, should not get here')
        return suggestions[:max_suggestions]

    def satisfy_available_fraction_obligation(self,
                                              suggestions: List[GeneratedName],
                                              min_suggestions: int,
                                              max_suggestions: int,
                                              min_available_fraction: float) -> List[GeneratedName]:
        """
        Function which tries to satisfy the requirement of minimal available names fraction in the returned suggestions.

        :param suggestions: aggregated list of generated names. Assuming it has only unique names
        :param min_suggestions: request parameter specifying minimal number of generated names
        :param max_suggestions: request parameter specifying maximal number of generated names
        :param min_available_fraction: request parameter specifying the minimal factor of available names in the result
        :return: list of generated names in which the part of available names either satisfies the requirement
            or maximizes its part
        """
        min_available_fraction = min(min_available_fraction, 1.0)

        assert len(suggestions) == len({str(s) for s in suggestions})  # asserting there are only unique names

        needed_available_count = int(math.ceil(min_available_fraction * min_suggestions))
        available_count = len([str(s) for s in suggestions[:max_suggestions] if s.status == 'available'])
        rest_available_count = len([str(s) for s in suggestions[max_suggestions:] if s.status == 'available'])

        if available_count >= needed_available_count:
            return suggestions[:max_suggestions]

        if available_count + rest_available_count < needed_available_count:
            logger.warning('not enough available suggestions generated '
                           f'({available_count + rest_available_count} out of {needed_available_count} needed)')

        # if available_count + rest_available_count is enough, then it will reach the required threshold
        # otherwise it will use as many available suggestions as we have
        return self.maximize_available_fraction(suggestions,
                                                needed_available_count=needed_available_count,
                                                max_suggestions=max_suggestions,
                                                all_available_count=available_count + rest_available_count)

    def sort(self,
             pipelines_suggestions: List[List[GeneratedName]],
             min_suggestions: int = None,
             max_suggestions: int = None,
             min_available_fraction: float = None) -> List[GeneratedName]:
        raise NotImplementedError
