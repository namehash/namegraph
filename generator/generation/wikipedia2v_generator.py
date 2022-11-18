import logging
import re
import sys
from typing import List, Tuple, Any
import gensim.downloader

from .name_generator import NameGenerator

logger = logging.getLogger('generator')


class Wikipedia2VGenerator(NameGenerator):
    """
    Find similar phrases using wikipedia2vec and treating input as ENTITY.
    """

    def __init__(self, config):
        super().__init__(config)
        try:
            self.model = gensim.models.keyedvectors.KeyedVectors.load(config.generation.wikipedia2vec_path)
        except FileNotFoundError as e:
            print('No embeddings in binary format. Run generator/download.py.', file=sys.stderr)
            raise FileNotFoundError('No embeddings in binary format. Run generator/download_from_s3.py.')

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        name = '_'.join(tokens)
        query = f'ENTITY/{name}'

        try:
            similar = self.model.most_similar(query, topn=self.limit)
        except KeyError:
            return []

        result = []
        for phrase, dist in similar:
            phrase = re.sub(r'^ENTITY/', '', phrase)
            phrase = re.sub(r'_\(.*\)$', '', phrase)  # remove disambiguations
            phrase = re.split(r'_', phrase)
            result.append(phrase)

        return [tuple(x) for x in result]
