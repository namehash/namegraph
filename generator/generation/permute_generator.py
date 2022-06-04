from typing import List, Dict, Tuple
import itertools

from .name_generator import NameGenerator


class PermuteGenerator(NameGenerator):
    """
    Generate permutations of tokens.
    """

    def __init__(self, config):
        super().__init__()
        self.limit = config.generation.limit_generator

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        return itertools.islice(itertools.permutations(tokens), self.limit)
