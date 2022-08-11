from .normalizer import Normalizer


class LongNameNormalizer(Normalizer):
    def __init__(self, config):
        self.name_length_limit = config.app.name_length_limit

    def normalize(self, name: str) -> str:
        return name[:self.name_length_limit]
