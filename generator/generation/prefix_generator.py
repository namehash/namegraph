from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..the_name import TheName, Interpretation


class PrefixGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, config):
        super().__init__(config)
        self.prefixes = [line.strip() for line in open(config.generation.prefixes_path)]

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        name = ''.join(tokens)
        return [tuple([prefix] + list(tokens)) for prefix in self.prefixes if not name.startswith(prefix)]

    def generate2(self, name: TheName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: TheName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,)}
