from typing import List, Dict, Tuple

from .name_generator import NameGenerator

class PrefixGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, prefixes):
        super().__init__()
        self.prefixes = prefixes

    def generate(self, tokens: Tuple[str]) -> List[Tuple[str]]:
        return [tuple([prefix] + list(tokens)) for prefix in self.prefixes]
