import collections
from typing import List, Tuple, Iterable, Dict, Any

import wordninja

from .name_generator import NameGenerator
from ..domains import Domains
from ..the_name import Interpretation, TheName
from ..utils import sort_by_value


class OnSaleMatchGenerator(NameGenerator):
    """
    Returns on sale names with at least one the same token.
    """

    def __init__(self, config):
        super().__init__(config)
        self.domains = Domains(config)
        # index names
        self.index = collections.defaultdict(set)
        for name in self.domains.on_sale:
            tokenized = tuple(wordninja.split(name))
            for token in tokenized:
                self.index[token].add((name,))

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        result = []
        for token in tokens:
            result.extend(self.index[token])
        return [(item,) for item in sort_by_value([r[0] for r in result], self.domains.on_sale, reverse=True)]

    def generate2(self, name: TheName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: TheName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
