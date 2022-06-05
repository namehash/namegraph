import re
from unidecode import unidecode


class Normalizer:
    def __init__(self, config):
        pass

    def normalize(self, name: str) -> str:
        for normalizer in [self.strip_eth, self.ignore_namehash, self.unicode_normalize, self.only_valid_characters,
                           self.ignore_short]:
            name = normalizer(name)
        return name

    def strip_eth(self, name: str) -> str:
        return name[:-4] if name.endswith('.eth') else name

    def unicode_normalize(self, name: str) -> str:
        # return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8') # dont work with ł
        return unidecode(name, errors='ignore').lower()

    def only_valid_characters(self, name: str) -> str:
        return re.sub(r'[^a-z0-9-]+', '', name)

    def ignore_short(self, name: str) -> str:
        return name if len(name) >= 3 else ''

    def ignore_namehash(self, name: str) -> str:
        return '' if re.match(r'^\[[0-9a-f]{64}\]$', name) else name
