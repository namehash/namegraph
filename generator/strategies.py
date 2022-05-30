import collections
import itertools
import math
from typing import List, Dict


class GeneratedName:
    def __init__(self, tokens: List[str], applied_strategies=None):
        self.tokens = tokens
        if applied_strategies is None:
            self.applied_strategies = []
        else:
            self.applied_strategies = applied_strategies  # history of applied strategies

    def __str__(self):
        return ''.join(self.tokens)


class Strategy:
    def __init__(self):
        pass

    def apply(self, tokenized_name: GeneratedName) -> List[GeneratedName]:
        return [GeneratedName(changed, tokenized_name.applied_strategies + [self.__class__.__name__]) for changed in
                self.generate(tokenized_name.tokens)]

    def generate(self, tokens: List[str]) -> List[List[str]]:
        pass


class Permute(Strategy):
    """
    Generate permutations of tokens.
    """

    def __init__(self):
        super().__init__()

    def generate(self, tokens: List[str]) -> List[List[str]]:
        return itertools.permutations(tokens)


class Prefix(Strategy):
    """
    Add prefix.
    """

    def __init__(self, prefixes):
        super().__init__()
        self.prefixes = prefixes

    def generate(self, tokens: List[str]) -> List[List[str]]:
        return [[prefix] + tokens for prefix in self.prefixes]


class Suffix(Strategy):
    """
    Add suffix.
    """

    def __init__(self, prefixes):
        super().__init__()
        self.suffixes = prefixes

    def generate(self, tokens: List[str]) -> List[List[str]]:
        return [tokens + [suffix] for suffix in self.suffixes]

import nltk
from nltk.corpus import wordnet as wn

class WordNetSynonyms(Strategy):
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

class Categories(Strategy):
    """
    Replace tokens using categories.
    """

    def __init__(self, categories: Dict[str,List[str]]):
        super().__init__()
        self.categories=categories
        self.inverted_categories =collections.defaultdict(list)
        for category, tokens in categories.items():
            for token in tokens:
                self.inverted_categories[token].append(category)

    def generate(self, tokens: List[str]) -> List[List[str]]:
        tokens_synsets = [self.get_similar(token) for token in tokens]

        names = []
        for asc in itertools.product(*[lemmas.items() for lemmas in tokens_synsets]):
            names.append(([token[0] for token in asc], sum([token[1] for token in asc])))

        return [x[0] for x in sorted(names, key=lambda x: x[1], reverse=True)]

    def get_similar(self, token: str) -> Dict[str, int]:
        stats = collections.defaultdict(int)
        stats[token] += 1
        for category in self.inverted_categories[token]:
            for token in self.categories[category]:
                stats[token]+=1
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

import gensim.downloader
class W2VSimilarity(Strategy):
    """
    Replace tokens using w2v similarity.
    """

    def __init__(self, model_path='glove-twitter-25'):
        super().__init__()
        self.model = gensim.downloader.load(model_path)

    def generate(self, tokens: List[str]) -> List[List[str]]:
        topn=int(100**(1/len(tokens)) + 1)
        
        tokens_synsets = []
        for token in tokens:
            try:
                tokens_synsets.append([(token,1.0)]+self.model.most_similar(token, topn=topn))
            except KeyError: #token not in embedding dictionary
                tokens_synsets.append([(token,1.0)])

        names = []
        for asc in itertools.product(*tokens_synsets):
            names.append(([token[0] for token in asc], sum([token[1] for token in asc]))) #TODO

        return [x[0] for x in sorted(names, key=lambda x: x[1], reverse=True)]
