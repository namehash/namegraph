from typing import List, Tuple

from .tokenizer import Tokenizer


class NoneTokenizer(Tokenizer):
    """Return the input without tokenization."""

    def __init__(self, config):
        super().__init__()

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        return [(name,)]
