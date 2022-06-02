from typing import List, Dict, Tuple
import math
import gensim.downloader
import itertools

from .name_generator import NameGenerator


class W2VGenerator(NameGenerator):
    """
    Replace tokens using word2vec similarity.
    """

    def __init__(self, config):
        super().__init__()
        self.model = gensim.downloader.load(config.generation.word2vec_model)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        topn = int(100 ** (1 / len(tokens)) + 1)

        tokens_synsets = []
        for token in tokens:
            try:
                tokens_synsets.append([(token, 1.0)] + self.model.most_similar(token, topn=topn))
            except KeyError:  # token not in embedding dictionary
                tokens_synsets.append([(token, 1.0)])

        names = []
        for asc in itertools.product(*tokens_synsets):
            names.append(([token[0] for token in asc], sum([token[1] for token in asc])))  # TODO

        return [tuple(x[0]) for x in sorted(names, key=lambda x: x[1], reverse=True)]
