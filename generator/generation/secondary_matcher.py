import collections
from typing import List, Tuple, Iterable, Dict, Any

import wordninja

from .name_generator import NameGenerator
from ..domains import Domains
from ..utils import sort_by_value


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
                self.index[token].add((name,))

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        result = []
        for token in tokens:
            result.extend(self.index[token])
        return [(item,) for item in sort_by_value([r[0] for r in result], self.domains.secondary_market, reverse=True)]
