from typing import List, Tuple, Any
from itertools import product, islice, chain

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation


class HyphenGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, config):
        super().__init__(config)

    def _apply_hyphens(self, tokens: Tuple[str, ...], flags: Tuple[bool]) -> Tuple[str, ...]:
        hyphens_count = sum(flags)
        generated_tokens = ['-'] * (len(tokens) + hyphens_count)

        idx = 0
        for token, flag in zip(tokens, flags):
            generated_tokens[idx] = token
            idx += 1 + flag
        generated_tokens[-1] = tokens[-1]

        return tuple(generated_tokens)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(tokens) <= 1:
            return []

        # `2 ** (len(tokens) - 1) - 1` means we cut off the last element (the one having all False and no hyphens)
        return [
            self._apply_hyphens(tokens, flags)
            for flags in
            islice(product((True, False), repeat=len(tokens) - 1), min(2 ** (len(tokens) - 1) - 1, self.limit))
        ]

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}