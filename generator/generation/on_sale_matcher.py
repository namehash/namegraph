import collections
from typing import List, Tuple, Iterable, Dict, Any

import wordninja

from .name_generator import NameGenerator
from ..domains import Domains
from ..input_name import Interpretation, InputName
from ..utils import sort_by_value


class OnSaleMatchGenerator(NameGenerator):
    """
    Returns on sale names with at least one the same token.
    """

    def __init__(self, config):
        super().__init__(config)
        self.domains = Domains(config)
        # index names
        self.index = collections.defaultdict(dict)
        for name in self.domains.on_sale:
            tokenized = tuple(wordninja.split(name))
            for token in tokenized:
                self.index[token][(name,)] = None

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        result = []
        for token in tokens:
            result.extend(self.index[token].keys())
        return [(item,) for item in sort_by_value([r[0] for r in result], self.domains.on_sale, reverse=True)]

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
