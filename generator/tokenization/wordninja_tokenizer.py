from typing import List, Tuple
from functools import lru_cache
import wordninja

from .tokenizer import Tokenizer


@lru_cache(64)
def _tokenizer(name: str) -> List[Tuple[str, ...]]:
    return [tuple(wordninja.split(name))]


class WordNinjaTokenizer(Tokenizer):
    """Return one the most probable tokenization."""

    def __init__(self, config):
        super().__init__()

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        return _tokenizer(name)
