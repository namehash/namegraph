from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..the_name import TheName, Interpretation


class SuffixGenerator(NameGenerator):
    """
    Add suffix.
    """

    def __init__(self, config):
        super().__init__(config)
        self.suffixes = [line.strip() for line in open(config.generation.suffixes_path)]

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        name = ''.join(tokens)
        return [tuple(list(tokens) + [suffix]) for suffix in self.suffixes if not name.endswith(suffix)]

    def generate2(self, name: TheName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: TheName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,)}
