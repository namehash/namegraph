import random, logging
from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..domains import Domains

logger = logging.getLogger('generator')


class OnlyPrimaryRandomGenerator(NameGenerator):
    """
    Sample only primary random names.
    """

    def __init__(self, config):
        super().__init__(config)
        self.domains = Domains(config)

        if len(self.domains.only_primary) < self.limit:
            logger.warning('the number of primary (available) domains for OnlyPrimaryRandomGenerator is smaller than '
                           'the generation limit')

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        if len(self.domains.only_primary) >= self.limit:
            result = random.sample(self.domains.only_primary, self.limit)
        else:
            result = self.domains.only_primary
        return [(x,) for x in result]
