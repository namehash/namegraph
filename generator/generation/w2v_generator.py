import json
import logging
import sys
from operator import itemgetter
from typing import List, Tuple, Any
import gensim.downloader
import itertools

import rocksdict
from rocksdict import AccessType

from .combination_limiter import CombinationLimiter, prod

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation

logger = logging.getLogger('generator')


class W2VGenerator(NameGenerator):
    """
    Replace tokens using word2vec similarity.
    """

    def __init__(self, config):
        super().__init__(config)
        # self.model = gensim.downloader.load(config.generation.word2vec_model)
        try:
            self.model: gensim.models.keyedvectors.KeyedVectors = \
                gensim.models.keyedvectors.KeyedVectors.load(config.generation.word2vec_path, mmap='r')
        except FileNotFoundError as e:
            print('No embeddings in binary format. Run generator/download.py.', file=sys.stderr)
            raise FileNotFoundError('No embeddings in binary format. Run generator/download.py.')
        self.combination_limiter = CombinationLimiter(self.limit)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

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
            distances = [t[1] for t in synset_tuple] #TODO speed up?
            result.append((tokens, prod(distances)))

        return (tuple(x[0]) for x in sorted(result, key=itemgetter(1), reverse=True))

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}




class W2VGeneratorRocks(NameGenerator):
    """
    Replace tokens using word2vec similarity.
    """

    def __init__(self, config):
        super().__init__(config)
        tokens_path = f'{config.generation.word2vec_rocks_path}/tokens.json'
        similar_path = f'{config.generation.word2vec_rocks_path}/similar.rocks'
        self.tokens = json.load(open(tokens_path, 'r'))
        self.token_to_id = {token: ind for ind, token in enumerate(self.tokens)}
        self.rockdb = rocksdict.Rdict(similar_path, access_type=AccessType.read_only())
        
        self.combination_limiter = CombinationLimiter(self.limit)

    def most_similar(self, token:str, topn:int):
        ind = self.token_to_id[token]
        similar = self.rockdb[ind][:topn]
        similar = [(self.tokens[i], d) for i, d in similar]
        return similar


    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        topn = int(10000 ** (1 / max(len(tokens), 1)) + 1)

        tokens_synsets = []
        for token in tokens:
            try:
                tokens_synsets.append([(token, 1.0)] + self.most_similar(token, topn=topn))
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
            distances = [t[1] for t in synset_tuple] #TODO speed up?
            result.append((tokens, prod(distances)))

        return (tuple(x[0]) for x in sorted(result, key=itemgetter(1), reverse=True))

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
