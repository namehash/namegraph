from typing import List, Tuple
from nltk.corpus import wordnet as wn


class BigramWordnetTokenizer():
    """Tokenize concatenation of two words from WordNet."""

    def __init__(self, config):
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
