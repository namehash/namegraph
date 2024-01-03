from typing import List, Tuple, Any

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation


class PrefixGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, config):
        super().__init__(config)
        self.prefixes = [line.strip() for line in open(config.generation.prefixes_path)]

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        name = ''.join(tokens)
        return (tuple([prefix] + list(tokens)) for prefix in self.prefixes if not name.startswith(prefix))

    async def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (
            name.strip_eth_namehash_unicode_replace_invalid_long_name
            or name.strip_eth_namehash_unicode
            or name.strip_eth_namehash,)}
