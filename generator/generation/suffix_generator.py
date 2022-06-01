from typing import List, Dict, Tuple

from .name_generator import NameGenerator

class SuffixGenerator(NameGenerator):
    """
    Add suffix.
    """

    def __init__(self, suffixes):
        super().__init__()
        self.suffixes = suffixes

    def generate(self, tokens: Tuple[str]) -> List[Tuple[str]]:
        return [tuple(list(tokens) + [suffix]) for suffix in self.suffixes]
