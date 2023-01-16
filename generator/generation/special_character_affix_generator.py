from typing import List, Tuple, Any

from .name_generator import NameGenerator


class SpecialCharacterAffixGenerator(NameGenerator):
    """

    """

    def __init__(self, config):
        super().__init__(config)

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        return [
            ('_',) + tokens,
            ('$',) + tokens,
            ('Ξ',) + tokens,
            tokens + ('Ξ',),
        ]
