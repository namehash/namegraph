import nltk
from nltk.corpus import wordnet as wn
from typing import List, Dict
import itertools
import collections

from .name_generator import NameGenerator

class WordnetSynonymsGenerator(NameGenerator):
    """
    Replace tokens with synonyms.
    """
    def __init__(self, config):
        nltk.download("wordnet")
        nltk.download("omw-1.4")
        wn.synsets('dog')  # init wordnet


    def generate(self, tokens: List[str]) -> List[List[str]]:
        result = []
        synsets = [self._get_lemmas_for_word(t).items() for t in tokens]
        for synset_tuple in itertools.product(*synsets):
            tokens = [t[0] for t in synset_tuple]
            counts = [t[1] for t in synset_tuple]
            result.append((tokens, sum(counts)))

        result = [tuple(x[0]) for x in sorted(result, key=lambda x: x[1], reverse=True)]
        return result

    def _get_lemmas_for_word(self, word: str) -> Dict[str, int]:
        synsets = wn.synsets(word)
        lemmas = []
        for synset in synsets:
            lemmas.extend([str(lemma.name()) for lemma in synset.lemmas()])
        lemmas = [l for l in lemmas if '_' not in l]

        stats = collections.defaultdict(int)
        for l in lemmas:
            stats[l] += 1

        # keep the original token in the output
        stats[word] += 1

        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

