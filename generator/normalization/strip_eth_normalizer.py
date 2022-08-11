from .normalizer import Normalizer


def strip_eth(name: str) -> str:
    return name[:-4] if name.endswith('.eth') else name


class StripEthNormalizer(Normalizer):
    def __init__(self, config):
        super().__init__()

    def normalize(self, name: str) -> str:
        return strip_eth(name)
