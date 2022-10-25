from typing import List, Tuple

from .name_generator import NameGenerator


class SpecialCharacterAffixGenerator(NameGenerator):
    """

    """

    def __init__(self, config):
        super().__init__()

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        return [('_',) + tokens, ('$',) + tokens]
