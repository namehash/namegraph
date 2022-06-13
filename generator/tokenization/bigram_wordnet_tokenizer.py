from typing import List, Tuple

import nltk
from nltk.corpus import wordnet as wn

from .tokenizer import Tokenizer


class BigramWordnetTokenizer(Tokenizer):
    """Tokenize concatenation of two words from WordNet."""

    def __init__(self, config):
        super().__init__()
        nltk.download("wordnet")
        nltk.download("omw-1.4")
        wn.synsets('dog')

    def tokenize(self, word: str) -> List[Tuple[str, ...]]:
        result = []
        if wn.synsets(word):
            result.append((word,))

        for i in range(1, len(word)):
            prefix_synsets = wn.synsets(word[:i])
            suffix_synsets = wn.synsets(word[i:])

            if prefix_synsets and suffix_synsets:
                result.append((word[:i], word[i:]))

        return result
