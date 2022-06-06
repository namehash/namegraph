import re


class ReplaceInvalidNormalizer:
    def __init__(self, config):
        pass

    def normalize(self, name: str) -> str:
        return re.sub(r'[^a-z0-9-]+', '', name)
