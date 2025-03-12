import re

from .normalizer import Normalizer


class ReplaceInvalidNormalizer(Normalizer):
    def __init__(self, config):
        super().__init__()

    def normalize(self, name: str) -> str:
        return re.sub(r'[^a-z0-9-]+', '', name)
