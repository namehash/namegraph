from nltk.corpus import wordnet as wn
from itertools import chain

from .tokenizer import Tokenizer


# todo: use custom dictionary?

class BigramLongestTokenizer(Tokenizer):
    """Tokenize concatenation of two words from WordNet (minimize abs(len(b1) - len(b2)) for b1, b2 tokenization)."""

    def __init__(self, config):
        super().__init__()
        wn.synsets('dog')
        self.min_token_len = 3

    def get_tokenization(self, word: str) -> tuple[str, str] | None:
        if len(word) < 2 * self.min_token_len:
            return None

        for i in self.generate_indices(word):
            prefix_synsets = wn.synsets(word[:i])
            suffix_synsets = wn.synsets(word[i:])
            if prefix_synsets and suffix_synsets:
                return word[:i], word[i:]

        if wn.synsets(word):
            return word, ''
        return None

    def generate_indices(self, iterable) -> list[int]:
        mid = len(iterable) // 2
        left_indices = list(reversed(range(mid)))
        right_indices = list(range(mid + 1, len(iterable)))
        limit = max(len(left_indices), len(right_indices)) - self.min_token_len
        return list(chain([mid], *zip(right_indices[:limit], left_indices[:limit])))
