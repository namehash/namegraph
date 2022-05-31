from typing import List, Dict
import math
import gensim.downloader
import itertools

from .name_generator import NameGenerator

class W2VGenerator(NameGenerator):
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
