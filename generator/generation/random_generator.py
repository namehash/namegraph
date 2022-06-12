import random
from typing import List, Tuple

from .name_generator import NameGenerator
from ..domains import Domains


class RandomGenerator(NameGenerator):
    """
    Sample random names.
    """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.domains = Domains(config)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        count = self.config.app.suggestions * 2
        if len(self.domains.internet) >= count:
            result = random.sample(self.domains.internet, count)
        else:
            result = self.domains.internet
        return [(x,) for x in result]
