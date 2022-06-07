import glob
import itertools, collections
import logging
from functools import reduce
from pathlib import Path
from typing import List, Dict, Tuple
from . import NameGenerator
from .combination_limiter import CombinationLimiter

logger = logging.getLogger('generator')


def load_categories(config):
    categories = collections.defaultdict(list)
    pattern = str(Path(config.app.categories) / '**/*.txt')
    for path in glob.iglob(pattern, recursive=True):
        with open(path) as category_file:
            for line in category_file:
                categories[path].append(line.strip())
    return categories


class CategoriesGenerator(NameGenerator):
    """
    Replace tokens using categories.
    """

    def __init__(self, config):
        super().__init__()
        self.categories: Dict[str, List[str]] = load_categories(config)
        self.inverted_categories = collections.defaultdict(list)
        for category, tokens in self.categories.items():
            for token in tokens:
                self.inverted_categories[token].append(category)
        self.combination_limiter = CombinationLimiter(config.generation.limit)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        tokens_synsets = [self.get_similar(token) for token in tokens]
        tokens_synsets = [list(lemmas.items()) for lemmas in tokens_synsets]

        tokens_synsets = self.combination_limiter.limit(tokens_synsets)

        synset_lengths = [len(synset) for synset in tokens_synsets]
        combinations = reduce((lambda x, y: x * y), synset_lengths)
        logger.debug(f'CategoriesGenerator synsets lengths: {synset_lengths} gives {combinations}')
        logger.debug(
            f'CategoriesGenerator synsets: {[[synset_tuple[0] for synset_tuple in synset][:100] for synset in tokens_synsets]}')

        result = []
        for synset_tuple in itertools.product(*tokens_synsets):
            tokens = [t[0] for t in synset_tuple]
            counts = [t[1] for t in synset_tuple]
            result.append((tokens, sum(counts)))

        return [tuple(x[0]) for x in sorted(result, key=lambda x: x[1], reverse=True)]

    def get_similar(self, token: str) -> Dict[str, int]:
        stats = collections.defaultdict(int)
        stats[token] += 1
        for category in self.inverted_categories[token]:
            for token in self.categories[category]:
                stats[token] += 1
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
