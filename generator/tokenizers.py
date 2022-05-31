import re
from typing import List

import wordninja
from nltk.corpus import wordnet as wn


class TwoWordWordNetTokenizer():
    """Tokenize concatenation of two words from WordNet."""

    def __init__(self):
        wn.synsets('dog')

    def tokenize(self, name: str) -> List[List[str]]:
        result = []
        if wn.synsets(name):
            result.append([name])

        for i in range(1, len(name)):
            prefix_synsets = wn.synsets(name[:i])
            suffix_synsets = wn.synsets(name[i:])

            if prefix_synsets and suffix_synsets:
                result.append([name[:i], name[i:]])

        return result


class TwoWordTokenizer():
    """Tokenize concatenation of two words from list of words."""

    # TODO: make recursive
    # TODO: use trie

    def __init__(self, path='/usr/share/dict/words'):
        self.words = set()
        with open(path) as f:
            for line in f:
                word = line.strip()
                if re.match(r'^\w+$', word):
                    self.words.add(word.lower())

    def tokenize(self, name: str) -> List[List[str]]:
        result = []
        if name in self.words:
            result.append([name])

        for i in range(1, len(name)):
            if name[:i] in self.words and name[i:] in self.words:
                result.append([name[:i], name[i:]])

        return result


class WordNinjaTokenizer():
    """Return one the most probable tokenization."""

    def __init__(self):
        pass

    def tokenize(self, name: str) -> List[List[str]]:
        return [wordninja.split(name)]
