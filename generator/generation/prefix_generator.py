from typing import List, Dict, Tuple

from .name_generator import NameGenerator


class PrefixGenerator(NameGenerator):
    """
    Add prefix.
    """

    def __init__(self, config):
        super().__init__()
        self.prefixes = set([line.strip() for line in open(config.generation.prefixes_path)])

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        name = ''.join(tokens)
        return [tuple([prefix] + list(tokens)) for prefix in self.prefixes if not name.startswith(prefix)]
