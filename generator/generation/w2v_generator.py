import logging
from functools import reduce
from typing import List, Dict, Tuple
import gensim.downloader
import itertools

from .name_generator import NameGenerator

logger = logging.getLogger('generator')


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

        synset_lengths = [len(synset) for synset in tokens_synsets]
        combinations = reduce((lambda x, y: x * y), synset_lengths)
        logger.debug(f'Word2vec synsets lengths: {synset_lengths} gives {combinations}')
        logger.debug(
            f'Word2vec synsets: {[[synset_tuple[0] for synset_tuple in synset][:100] for synset in tokens_synsets]}')

        result = []
        for synset_tuple in itertools.product(*tokens_synsets):
            tokens = [t[0] for t in synset_tuple]
            distances = [t[1] for t in synset_tuple]
            result.append((tokens, sum(distances)))  # TODO multiply distances?

        return [tuple(x[0]) for x in sorted(result, key=lambda x: x[1], reverse=True)]
