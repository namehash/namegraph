from typing import List, Tuple, Any
from itertools import product, islice
import re

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation


class AbbreviationGenerator(NameGenerator):
    """
    Returns all the possibilities of different tokens replaced with their abbreviation except the situation,
    in which no token is replaced.
    """

    def __init__(self, config):
        super().__init__(config)
        self.word_regex = re.compile(r'[a-zA-Z]{2,}')

    def _apply_abbreviations(self, tokens: Tuple[str, ...], flags: Tuple[bool], is_word: Tuple[bool]) -> Tuple[
        str, ...]:
        abbrev_tokens = list(tokens)
        i = 0
        for idx, (token, word_token) in enumerate(zip(tokens, is_word)):
            if word_token:
                if flags[i]:
                    abbrev_tokens[idx] = token[0]
                i += 1

        return tuple(abbrev_tokens)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        word_tokens = tuple([True if self.word_regex.fullmatch(token) else False for token in tokens])
        all_flags_generator = islice(product((False, True), repeat=sum(word_tokens)), 1, self.limit)
        all_flags = sorted(all_flags_generator, key=sum)
        return (
            self._apply_abbreviations(tokens, flags, word_tokens)
            for flags in all_flags
        )

    async def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
