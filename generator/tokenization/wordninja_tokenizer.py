from typing import List, Tuple
import wordninja

from .tokenizer import Tokenizer


class WordNinjaTokenizer(Tokenizer):
    """Return one the most probable tokenization."""

    def __init__(self, config):
        super().__init__()

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        return [tuple(wordninja.split(name))]
