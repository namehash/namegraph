from typing import List
import logging, math

from omegaconf import DictConfig

from generator.generated_name import GeneratedName


logger = logging.getLogger('generator')


class Sorter:
    def __init__(self, config: DictConfig):
        self.config = config

    def maximize_primary_fraction(self,
                                  suggestions: List[GeneratedName],
                                  min_suggestions: int,
                                  max_suggestions: int,
                                  all_primary_count: int = None) -> List[GeneratedName]:

        if all_primary_count is None:
            all_primary_count = len([str(s) for s in suggestions if s.category == 'primary'])

        primary_used = 0
        for i, s in enumerate(suggestions):
            if s.category == 'primary':
                primary_used += 1

            # if there is just enough space left for all the left primary suggestions we simply append them at the end
            if max_suggestions - i == all_primary_count - primary_used:
                rest_primary = [s for s in suggestions[i:] if s.category == 'primary']
                assert len(rest_primary) == all_primary_count - primary_used

                return suggestions[:i] + rest_primary

        logger.warning('weird parameters used, should not get here')
        return suggestions[:max_suggestions]

    def satisfy_primary_fraction_obligation(self,
                                            suggestions: List[GeneratedName],
                                            min_suggestions: int,
                                            max_suggestions: int) -> List[GeneratedName]:
        """
        Function which tries to satisfy the requirement of minimal primary names fraction in the returned suggestions.

        :param suggestions: aggregated list of generated names. Assuming it has only unique names
        :param min_suggestions: request parameter specifying minimal number of generated names
        :param max_suggestions: request parameter specifying maximal number of generated names
        :return: list of generated names in which the part of primary names either satisfies the requirement
            or maximizes its part
        """

        assert len(suggestions) == len({str(s) for s in suggestions})  # asserting there are only unique names

        needed_primary_count = int(math.ceil(self.config.app.min_primary_fraction * min_suggestions))
        primary_count = len([str(s) for s in suggestions[:max_suggestions] if s.category == 'primary'])
        rest_primary_count = len([str(s) for s in suggestions[max_suggestions:] if s.category == 'primary'])

        if primary_count >= needed_primary_count:
            return suggestions[:max_suggestions]

        if primary_count + rest_primary_count < needed_primary_count:
            logger.warning('not enough primary suggestions generated '
                           f'({primary_count + rest_primary_count} out of {needed_primary_count} needed)')

        # if primary_count + rest_primary_count is enough, then it will reach the required threshold
        # otherwise it will use as many primary suggestions as we have
        return self.maximize_primary_fraction(suggestions,
                                              min_suggestions=min_suggestions,
                                              max_suggestions=max_suggestions,
                                              all_primary_count=primary_count + rest_primary_count)

    def sort(self,
             pipelines_suggestions: List[List[GeneratedName]],
             min_suggestions: int = None,
             max_suggestions: int = None) -> List[GeneratedName]:
        raise NotImplementedError
