from typing import List, Dict

from .name_generator import NameGenerator

class SuffixGenerator(NameGenerator):
    """
    Add suffix.
    """

    def __init__(self, suffixes):
        super().__init__()
        self.suffixes = suffixes

    def generate(self, tokens: List[str]) -> List[List[str]]:
        return [tokens + [suffix] for suffix in self.suffixes]
