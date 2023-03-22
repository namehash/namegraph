import csv
import math
from typing import Optional

from .pickle_cache import pickled_property
from .utils import ln

ALPHA = 0.4


class Ngrams:
    """Word probability of unigrams and bigrams."""

    def __init__(self, config):
        self.config = config

        if not config.ngrams.lazy_loading:
            self._unigrams_and_count
            self._bigrams_and_count

    def _load_string_and_count(self, path: str) -> tuple[dict[str, int], int]:
        data: dict[str, int] = {}
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            all_count = 0
            for row in reader:
                word, count = row
                count = int(count)
                all_count += count
                data[word] = count
        return data, all_count

    @pickled_property(
        'ngrams.unigrams',
        'ngrams.custom_dictionary',
        'ngrams.domain_specific_dictionary',
        'ngrams.custom_token_frequency'
    )
    def _unigrams_and_count(self) -> tuple[dict[str, int], int]:
        data, all_count = self._load_string_and_count(self.config.ngrams.unigrams)
        with open(self.config.ngrams.custom_dictionary) as f:
            for line in f:
                word = line.strip().lower()
                if word not in data:
                    data[word] = self.config.ngrams.custom_token_frequency

        with open(self.config.ngrams.domain_specific_dictionary) as f:
            for line in f:
                word = line.strip().lower()
                data[word] = max(data.get(word, self.config.ngrams.custom_token_frequency),
                                 self.config.ngrams.custom_token_frequency)

        return data, all_count

    @pickled_property('ngrams.bigrams')
    def _bigrams_and_count(self) -> tuple[dict[str, int], int]:
        return self._load_string_and_count(self.config.ngrams.bigrams)

    @property
    def unigrams(self) -> dict[str, int]:
        return self._unigrams_and_count[0]

    @property
    def bigrams(self) -> dict[str, int]:
        return self._bigrams_and_count[0]

    @property
    def all_unigrams_count(self) -> int:
        return self._unigrams_and_count[1]

    @property
    def all_bigrams_count(self) -> int:
        return self._bigrams_and_count[1]

    def unigram_count(self, word: str) -> int:
        return self.unigrams.get(word, self.oov_count(word))

    def bigram_count(self, word: str) -> Optional[int]:
        return self.bigrams.get(word, None)

    def oov_count(self, word: str) -> int:
        return (1 / 100) ** (len(word))

    def word_probability(self, word: str) -> float:
        return self.unigram_count(word) / self.all_unigrams_count

    def bigram_probability(self, word1: str, word2: str) -> float:
        bigram = f'{word1} {word2}'
        bigram_count = self.bigram_count(bigram)
        if bigram_count is not None:
            return bigram_count / self.unigram_count(word1)
        return ALPHA * self.word_probability(word2)

    def sequence_log_probability(self, words: list[str]) -> float:
        probs = [ln(self.word_probability(words[0]))] \
                + [ln(self.bigram_probability(word1, word2)) for word1, word2 in zip(words, words[1:])]
        return sum(probs)

    def sequence_probability(self, words: list[str]) -> float:
        return math.exp(self.sequence_log_probability(words))
