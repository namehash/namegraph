from typing import List, Tuple
from itertools import product, islice

from .name_generator import NameGenerator


class AbbreviationGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.limit = self.config.generation.limit

    def _apply_abbreviations(self, tokens: Tuple[str, ...], flags: Tuple[bool]) -> Tuple[str, ...]:
        return tuple([
            token[0] if flag else token
            for token, flag in zip(tokens, flags)
        ])

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        return [
            self._apply_abbreviations(tokens, flags)
            for flags in islice(product((False, True), repeat=len(tokens)), 1, self.limit)
        ]
