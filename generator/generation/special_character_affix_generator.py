from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..the_name import TheName, Interpretation


class SpecialCharacterAffixGenerator(NameGenerator):
    """

    """

    def __init__(self, config):
        super().__init__(config)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        return [
            ('_',) + tokens,
            ('$',) + tokens,
            ('Ξ',) + tokens,
            tokens + ('Ξ',),
        ]

    def generate2(self, name: TheName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: TheName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,)}