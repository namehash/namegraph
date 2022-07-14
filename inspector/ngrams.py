import csv
from math import log, e
from typing import List, Dict

OOV_COUNT = 1


class Ngrams:
    """For now it uses only unigrams."""

    def __init__(self, config):
        self._load_unigrams(config.inspector.unigrams)

    def _load_unigrams(self, path):
        self.unigrams: Dict[str, int] = {}
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            self.all_count = 0
            for row in reader:
                word, count = row
                count = int(count)
                self.all_count += count
                self.unigrams[word] = count

    def word_count(self, word: str) -> int:
        return self.unigrams.get(word, OOV_COUNT)

    def word_probability(self, word: str) -> float:
        return self.word_count(word) / self.all_count

    def sequence_probability(self, words: List[str]) -> float:
        probs = [log(self.word_probability(word)) for word in words]
        return e ** sum(probs)
