from typing import List, Dict
import itertools

from .name_generator import NameGenerator

class PermuteGenerator(NameGenerator):
    """
    Generate permutations of tokens.
    """

    def __init__(self):
        super().__init__()

    def generate(self, tokens: List[str]) -> List[List[str]]:
        return itertools.permutations(tokens)
