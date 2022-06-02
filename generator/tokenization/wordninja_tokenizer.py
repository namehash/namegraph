from typing import List
import wordninja


class WordNinjaTokenizer():
    """Return one the most probable tokenization."""

    def __init__(self, config):
        pass

    def tokenize(self, name: str) -> List[List[str]]:
        return [wordninja.split(name)]
