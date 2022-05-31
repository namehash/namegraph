from typing import List, Dict

from .name_generator import NameGenerator

class PrefixGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, prefixes):
        super().__init__()
        self.prefixes = prefixes

    def generate(self, tokens: List[str]) -> List[List[str]]:
        return [[prefix] + tokens for prefix in self.prefixes]
