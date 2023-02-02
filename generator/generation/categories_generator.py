import csv
import glob
import itertools, collections
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any
from . import NameGenerator
from .combination_limiter import CombinationLimiter, prod
from ..input_name import InputName, Interpretation

logger = logging.getLogger('generator')


def load_categories_from_csv(config):
    path = config.app.clubs
    categories = collections.defaultdict(list)
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            assert len(row) == 2
            name, category = row
            categories[category].append(name)
    return categories


def load_categories(config):
    categories = collections.defaultdict(list)

    ignored = [line.strip() for line in open(config.app.categories_ignored)]
    pattern = str(Path(config.app.categories) / '**/*.*')
    for path in glob.iglob(pattern, recursive=True):
        if any([i in path for i in ignored]):
            logger.debug(f'Ignore category {path}')
            continue
        if path.endswith('.txt'):
            with open(path) as category_file:
                for line in category_file:
                    name = line.strip()
                    if name: categories[path].append(name)
        elif path.endswith('.csv'):
            with open(path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    name = row[0].strip()
                    if name: categories[path].append(name)
        else:
            logger.warning(f"Categories cannot be read from file: {path}")
    return categories


def remove_duplicated_categories(categories):
    s = collections.defaultdict(list)
    for path, tokens in categories.items():
        s[tuple(sorted(tokens))].append(path)

    for paths in s.values():
        for path in paths[1:]:
            del categories[path]


class CategoriesGenerator(NameGenerator):
    """
    Replace tokens using categories.
    """

    def __init__(self, config):
        super().__init__(config)
        self.categories: Dict[str, List[str]] = load_categories_from_csv(config)
        # remove_duplicated_categories(self.categories)

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
        combinations = prod(synset_lengths)
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

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,)}
