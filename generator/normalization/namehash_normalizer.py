import re

from .normalizer import Normalizer


class NamehashNormalizer(Normalizer):
    def __init__(self, config):
        super().__init__()

    def normalize(self, name: str) -> str:
        return '' if re.match(r'^\[[0-9a-f]{64}\]$', name) else name
