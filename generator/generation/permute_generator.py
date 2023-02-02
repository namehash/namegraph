from typing import List, Tuple, Any
import itertools

from .name_generator import NameGenerator
from ..input_name import Interpretation, InputName


class PermuteGenerator(NameGenerator):
    """
    Generate permutations of tokens.
    """

    def __init__(self, config):
        super().__init__(config)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        return itertools.islice(itertools.permutations(tokens), self.limit)

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
