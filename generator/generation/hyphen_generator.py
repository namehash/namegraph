from typing import List, Tuple
from itertools import product, islice, chain

from .name_generator import NameGenerator


class HyphenGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.limit = self.config.generation.limit

    def _apply_hyphens(self, tokens: Tuple[str, ...], flags: Tuple[bool]) -> Tuple[str, ...]:
        hyphens = ['-' if flag else '' for flag in flags] + ['']
        return tuple([token for token in chain.from_iterable(zip(tokens, hyphens)) if token])

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        return [
            self._apply_hyphens(tokens, flags)
            for flags in islice(product((False, True), repeat=len(tokens)-1), 1, self.limit)
        ]