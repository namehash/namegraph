import csv

import itertools
import collections
import logging
import random

from operator import itemgetter
from typing import List, Dict, Tuple

from more_itertools import roundrobin
from omegaconf import DictConfig

from . import NameGenerator
from .combination_limiter import CombinationLimiter, prod
from ..input_name import InputName, Interpretation
from ..utils import Singleton
from namegraph.thread_utils import get_random_rng


logger = logging.getLogger('namegraph')


class Categories(metaclass=Singleton):
    def __init__(self, config: DictConfig) -> None:
        self.categories = self.load_categories_from_csv(config)
        self.inverted_categories = collections.defaultdict(list)
        for category, tokens in self.categories.items():
            for token in tokens:
                self.inverted_categories[token].append(category)

        random.seed(0)
        for tokens in self.categories.values():
            random.shuffle(tokens)

    def get_names(self, category: str) -> list[str]:
        return self.categories.get(category, [])

    def get_categories(self, name: str) -> list[str]:
        return self.inverted_categories.get(name, [])

    @staticmethod
    def load_categories_from_csv(config):
        path = config.app.clubs
        categories = collections.defaultdict(list)
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                assert len(row) == 2
                name, category = row
                categories[category].append(name.removesuffix('.eth'))
        return categories


class CategoriesGenerator(NameGenerator):
    """
    Replace tokens using categories. Faster, single token version.
    """

    def __init__(self, config):
        super().__init__(config)
        self.categories = Categories(config)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        token = ''.join(tokens)

        rng = get_random_rng()

        iterators = []
        for category in self.categories.get_categories(token):
            names = self.categories.get_names(category)
            start_index = rng.randint(0, len(names))
            iterators.append(
                itertools.chain(itertools.islice(names, start_index, None), itertools.islice(names, 0, start_index)))

        return ((s,) for s in roundrobin(*iterators))

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,)}


class MultiTokenCategoriesGenerator(NameGenerator):
    """
    Replace tokens using categories.
    """

    def __init__(self, config):
        super().__init__(config)
        self.categories = Categories(config)
        self.combination_limiter = CombinationLimiter(config.generation.limit)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        tokens_synsets = [self.get_similar(token) for token in tokens]
        tokens_synsets = [list(lemmas.items()) for lemmas in tokens_synsets]

        tokens_synsets = self.combination_limiter.limit(tokens_synsets)

        synset_lengths = [len(synset) for synset in tokens_synsets]
        combinations = prod(synset_lengths)
        logger.debug(f'CategoriesGenerator synsets lengths: {synset_lengths} gives {combinations}')
        logger.debug(
            f'CategoriesGenerator synsets: {[[synset_tuple[0] for synset_tuple in synset][:100] for synset in tokens_synsets]}')

        result = []
        for synset_tuple in itertools.product(*tokens_synsets):
            tokens = [t[0] for t in synset_tuple]
            counts = [t[1] for t in synset_tuple]
            result.append((tokens, sum(counts)))

        return (tuple(x[0]) for x in sorted(result, key=itemgetter(1), reverse=True))

    def get_similar(self, token: str) -> Dict[str, int]:
        stats = collections.defaultdict(int)
        stats[token] += 1
        for category in self.categories.get_categories(token):
            for token in self.categories.get_names(category):
                stats[token] += 1
        return dict(sorted(stats.items(), key=itemgetter(1), reverse=True))

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,)}
