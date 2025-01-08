from unidecode import unidecode

from .normalizer import Normalizer


class UnicodeNormalizer(Normalizer):
    def __init__(self, config):
        super().__init__()

    def normalize(self, name: str) -> str:
        return unidecode(name, errors='ignore').lower()
