import random, logging
from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..domains import Domains

logger = logging.getLogger('generator')


class RandomGenerator(NameGenerator):
    """
    Sample random names.
    """

    def __init__(self, config):
        super().__init__(config)
        self.domains = Domains(config)

        if len(self.domains.internet) < self.limit:
            logger.warning('the number of internet domains for random generator is smaller than the generation limit')

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        if len(self.domains.internet) >= self.limit:
            result = random.sample(self.domains.internet, self.limit)
        else:
            result = self.domains.internet
        return [(x,) for x in result]
