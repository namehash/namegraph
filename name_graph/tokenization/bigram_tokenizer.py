from typing import List, Tuple

from .tokenizer import Tokenizer


class BigramTokenizer(Tokenizer):
    def __init__(self, config):
        super().__init__()

    def tokenize(self, word: str) -> List[Tuple[str, ...]]:
        result = []
        for i in range(1, len(word)):
            prefix = word[:i]
            suffix = word[i:]
            result.append((prefix, suffix))

        return result
