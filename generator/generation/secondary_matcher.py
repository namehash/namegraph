import collections
from typing import List, Dict, Tuple

import wordninja

from .name_generator import NameGenerator
from ..domains import Domains


class SecondaryMatcher(NameGenerator):
    """
    
    """

    def __init__(self, config):
        super().__init__()
        self.domains = Domains(config)
        # index names
        self.index = collections.defaultdict(set)
        for name in self.domains.secondary_market:
            tokenized = tuple(wordninja.split(name))
            for token in tokenized:
                self.index[token].add(tokenized)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        result = []
        for token in tokens:
            result.extend(self.index[token])
        return result
