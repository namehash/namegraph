import re


class NamehashNormalizer:
    def __init__(self, config):
        pass

    def normalize(self, name: str) -> str:
        return '' if re.match(r'^\[[0-9a-f]{64}\]$', name) else name
