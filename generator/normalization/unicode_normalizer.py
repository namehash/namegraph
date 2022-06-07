from unidecode import unidecode


class UnicodeNormalizer:
    def __init__(self, config):
        pass

    def normalize(self, name: str) -> str:
        return unidecode(name, errors='ignore').lower()
