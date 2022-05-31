import nltk
from nltk.corpus import wordnet as wn
import itertools
import collections

class WordnetGenerator:
    def __init__(self, config):
        nltk.download("wordnet")
        nltk.download("omw-1.4")


    def generate(self, tokens):
        result = []
        synsets = [self._get_lemmas_for_word(t).items() for t in tokens]
        for synset_tuple in itertools.product(*synsets):
            tokens = [t[0] for t in synset_tuple]
            counts = [t[1] for t in synset_tuple]
            result.append((''.join(tokens), sum(counts)))

        return result

    def _get_lemmas_for_word(self, word):
        synsets = wn.synsets(word)
        return self._get_lemmas(synsets)

    def _get_lemmas(self, synsets):
        lemmas = []
        for synset in synsets:
            lemmas.extend([str(lemma.name()) for lemma in synset.lemmas()])
        lemmas = [l for l in lemmas if '_' not in l]

        stats = collections.defaultdict(int)
        for l in lemmas:
            stats[l] += 1

        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
