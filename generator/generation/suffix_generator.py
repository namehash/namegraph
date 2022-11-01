from typing import List, Tuple, Any

from .name_generator import NameGenerator


class SuffixGenerator(NameGenerator):
    """
    Add suffix.
    """

    def __init__(self, config):
        super().__init__()
        self.suffixes = [line.strip() for line in open(config.generation.suffixes_path)]

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        name = ''.join(tokens)
        return [tuple(list(tokens) + [suffix]) for suffix in self.suffixes if not name.endswith(suffix)]
