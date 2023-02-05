from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation


class KeycapGenerator(NameGenerator):
    """
    Change letters to squared letters.
    """

    def __init__(self, config):
        super().__init__(config)
        self.mapping = {
            # 'a': '🅰', 'b': '🅱', # commented because have different beautified version
            'c': '🅲', 'd': '🅳', 'e': '🅴', 'f': '🅵', 'g': '🅶', 'h': '🅷', 'i': '🅸', 'j': '🅹',
            'k': '🅺', 'l': '🅻', 'm': '🅼', 'n': '🅽', 
            # 'o': '🅾', 'p': '🅿', # commented because have different beautified version
            'q': '🆀', 'r': '🆁', 's': '🆂', 't': '🆃',
            'u': '🆄', 'v': '🆅', 'w': '🆆', 'x': '🆇', 'y': '🆈', 'z': '🆉',
            '0': '0⃣', '1': '1⃣', '2': '2⃣', '3': '3⃣', '4': '4⃣', '5': '5⃣', '6': '6⃣', '7': '7⃣', '8': '8⃣', '9': '9⃣'
        }

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        name = ''.join(tokens)
        try:
            return ((''.join([self.mapping[char] for char in name]),))
        except KeyError:
            return []
    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,)}