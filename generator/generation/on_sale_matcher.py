import collections
from typing import List, Tuple, Iterable, Dict, Any, Iterator

import wordninja

from .name_generator import NameGenerator
from ..domains import Domains
from ..input_name import Interpretation, InputName
from ..utils import sort_by_value_under_key


class OnSaleMatchGenerator(NameGenerator):
    """
    Returns on sale names with at least one the same token.
    """

    def __init__(self, config):
        super().__init__(config)
        self.domains = Domains(config)
        self.tokenizer = wordninja.LanguageModel(config.tokenization.wordninja_dictionary)
        # index names
        self.index = collections.defaultdict(dict)
        for name in self.domains.on_sale:
            tokenized = tuple(self.tokenizer.split(name))
            for token in tokenized:
                self.index[token][(name, tokenized)] = None

    def generate(self, tokens: Tuple[str, ...]) -> Iterator[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        result = []
        for token in tokens:
            result.extend(self.index[token].keys())
        return (item[1] for item in sort_by_value_under_key(result, self.domains.on_sale, sort_key=0, reverse=True))

    async def generate2(self, name: InputName, interpretation: Interpretation) -> Iterator[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
