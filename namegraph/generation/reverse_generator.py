from typing import Tuple, Iterator

from namegraph.generation import NameGenerator
from ..input_name import InputName, Interpretation



class ReverseGenerator(NameGenerator):
    """
    Return a reversed name.
    """

    def __init__(self, config):
        super().__init__(config)

    def generate(self, tokens: Tuple[str, ...]) -> Iterator[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []
        reversed_name = ''.join(tokens)[::-1]
        yield (reversed_name,)

    def generate2(self, name: InputName, interpretation: Interpretation) -> Iterator[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (
            name.strip_eth_namehash_unicode_replace_invalid_long_name
            or name.strip_eth_namehash_unicode
            or name.strip_eth_namehash,)}
