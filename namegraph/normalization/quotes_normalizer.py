from .normalizer import Normalizer


class QuotesNormalizer(Normalizer):
    def __init__(self, config):
        super().__init__()

    def normalize(self, name: str) -> str:
        if name.startswith('"') and name.endswith('"'):
            return name[1:-1].strip()
        else:
            return name
