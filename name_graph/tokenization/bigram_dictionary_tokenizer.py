import re
from typing import List, Tuple

from .tokenizer import Tokenizer


class BigramDictionaryTokenizer(Tokenizer):
    """Tokenize concatenation of two words from list of words."""

    # TODO: make recursive
    # TODO: use trie

    def __init__(self, config):
        super().__init__()
        path = config.tokenization.dictionary
        self.words = set()
        with open(path) as f:
            for line in f:
                word = line.strip()
                if re.match(r'^\w+$', word):
                    self.words.add(word.lower())

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        result = []
        if name in self.words:
            result.append((name,))

        for i in range(1, len(name)):
            if name[:i] in self.words and name[i:] in self.words:
                result.append((name[:i], name[i:]))

        return result
