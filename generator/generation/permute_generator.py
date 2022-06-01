from typing import List, Dict, Tuple
import itertools

from .name_generator import NameGenerator

class PermuteGenerator(NameGenerator):
    """
    Generate permutations of tokens.
    """

    def __init__(self):
        super().__init__()

    def generate(self, tokens: Tuple[str]) -> List[Tuple[str]]:
        return itertools.permutations(tokens)
