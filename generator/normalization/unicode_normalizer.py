from unidecode import unidecode


class UnicodeNormalizer:
    def __init__(self, config):
        pass

    def normalize(self, name: str) -> str:
        # return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8') # dont work with ł
        return unidecode(name, errors='ignore').lower()
