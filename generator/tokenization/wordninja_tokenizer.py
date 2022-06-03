from typing import List, Tuple
import wordninja


class WordNinjaTokenizer():
    """Return one the most probable tokenization."""

    def __init__(self, config):
        pass

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        return [tuple(wordninja.split(name))]
