from typing import List, Tuple, Any
import itertools

from .name_generator import NameGenerator


class PermuteGenerator(NameGenerator):
    """
    Generate permutations of tokens.
    """

    def __init__(self, config):
        super().__init__()
        self.limit = config.generation.limit

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        return itertools.islice(itertools.permutations(tokens), self.limit)
