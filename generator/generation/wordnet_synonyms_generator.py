import nltk
from nltk.corpus import wordnet as wn
from typing import List, Dict
import collections
import itertools

from .name_generator import NameGenerator

class WordNetSynonymsGenerator(NameGenerator):
    """
    Replace tokens with synonyms. #TODO hypernyms
    """

    def __init__(self):
        super().__init__()
        nltk.download("wordnet")
        nltk.download("omw-1.4")
        wn.synsets('dog')  # init wordnet


    def generate(self, tokens: List[str]) -> List[List[str]]:
        tokens_synsets = [self.get_lemmas(token) for token in tokens]

        names=[]
        for asc in  itertools.product(*[lemmas.items() for lemmas in tokens_synsets]):
            names.append(([token[0] for token in asc], sum([token[1] for token in asc])))

        return [x[0] for x in sorted(names, key=lambda x: x[1], reverse=True)]

    def get_lemmas(self, token: str) -> Dict[str, int]:
        synsets=wn.synsets(token)
        lemmas = []
        for synset in synsets:
            lemmas.extend([str(lemma.name()) for lemma in synset.lemmas()])
        lemmas = [l for l in lemmas if '_' not in l]

        stats = collections.defaultdict(int)
        for l in lemmas:
            stats[l] += 1

        stats[token]+=1 # keep token if lemma not found TODO: create version without?

        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
