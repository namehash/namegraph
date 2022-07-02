import logging
import sys
from typing import List, Dict, Tuple
import gensim.downloader
import itertools

from .combination_limiter import CombinationLimiter, prod

from .name_generator import NameGenerator

logger = logging.getLogger('generator')


class W2VGenerator(NameGenerator):
    """
    Replace tokens using word2vec similarity.
    """

    def __init__(self, config):
        super().__init__()
        # self.model = gensim.downloader.load(config.generation.word2vec_model)
        try:
            self.model = gensim.models.keyedvectors.KeyedVectors.load(config.generation.word2vec_path)
        except FileNotFoundError as e:
            print('No embeddings in binary format. Run generator/download.py.', file=sys.stderr)
            raise FileNotFoundError('No embeddings in binary format. Run generator/download.py.')
        self.combination_limiter = CombinationLimiter(config.generation.limit)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        topn = int(10000 ** (1 / max(len(tokens), 1)) + 1)

        tokens_synsets = []
        for token in tokens:
            try:
                tokens_synsets.append([(token, 1.0)] + self.model.most_similar(token, topn=topn))
            except KeyError:  # token not in embedding dictionary
                tokens_synsets.append([(token, 1.0)])

        synset_lengths = [len(synset) for synset in tokens_synsets]
        combinations = prod(synset_lengths)
        logger.debug(f'Word2vec synsets lengths: {synset_lengths} gives {combinations}')
        logger.debug(
            f'Word2vec synsets: {[[synset_tuple[0] for synset_tuple in synset][:100] for synset in tokens_synsets]}')

        tokens_synsets = self.combination_limiter.limit(tokens_synsets)

        result = []
        for synset_tuple in itertools.product(*tokens_synsets):
            tokens = [t[0] for t in synset_tuple]
            distances = [t[1] for t in synset_tuple]
            result.append((tokens, prod(distances)))

        return [tuple(x[0]) for x in sorted(result, key=lambda x: x[1], reverse=True)]
