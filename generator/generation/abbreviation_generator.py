from typing import List, Tuple, Any
from itertools import product, islice
import re

from .name_generator import NameGenerator


class AbbreviationGenerator(NameGenerator):
    """
    Returns all the possibilities of different tokens replaced with their abbreviation except the situation,
    in which no token is replaced.
    """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.limit = self.config.generation.limit
        self.word_regex = re.compile(r'[a-zA-Z]+')

    def _apply_abbreviations(self, tokens: Tuple[str, ...], flags: Tuple[bool], is_word: Tuple[bool]) -> Tuple[str, ...]:
        flags = iter(flags)
        return tuple([
            token[0] if word_token and next(flags) else token
            for token, word_token in zip(tokens, is_word)
        ])

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        word_tokens = tuple([True if self.word_regex.fullmatch(token) else False for token in tokens])
        all_flags_generator = islice(product((False, True), repeat=sum(word_tokens)), 1, self.limit)
        all_flags = sorted(all_flags_generator, key=sum)
        return [
            self._apply_abbreviations(tokens, flags, word_tokens)
            for flags in all_flags
        ]
