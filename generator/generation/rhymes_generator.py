from typing import Tuple, Iterator

from generator.generation import NameGenerator
from ..input_name import InputName, Interpretation


class RhymesGenerator(NameGenerator):
    """
    Yields names rhyming with the name.
    """

    def __init__(self, config):
        super().__init__(config)

    def generate(self, tokens: Tuple[str, ...]) -> Iterator[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        # todo

        yield ('rhyming_name',)

    def generate2(self, name: InputName, interpretation: Interpretation) -> Iterator[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid_long_name,)}
