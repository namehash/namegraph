from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation


class SpecialCharacterAffixGenerator(NameGenerator):
    """

    """

    def __init__(self, config):
        super().__init__(config)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        results = [('_',) + tokens, ('$',) + tokens]
        if all([token.isascii() for token in tokens]):
            results.extend([('ξ',) + tokens, tokens + ('ξ',)])
        return results

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid
                           or name.strip_eth_namehash_unicode
                           or name.strip_eth_namehash,)}
