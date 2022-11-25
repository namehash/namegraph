from typing import List, Tuple, Any

from .name_generator import NameGenerator


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

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        name = ''.join(tokens)
        try:
            return [(''.join([self.mapping[char] for char in name]),)]
        except KeyError:
            return []
