import csv
import glob
import itertools, collections
import logging
from functools import reduce
from pathlib import Path
from typing import List, Dict, Tuple
from . import NameGenerator

logger = logging.getLogger('generator')


def load_categories(config):
    categories = collections.defaultdict(list)
    pattern = str(Path(config.app.categories) / '**/*.*')
    for path in glob.iglob(pattern, recursive=True):
        if path.endswith('.txt'):
            with open(path) as category_file:
                for line in category_file:
                    categories[path].append(line.strip())
        elif path.endswith('.csv'):
            with open(path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    categories[path].append(row[0].strip())
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
        super().__init__()
        self.categories: Dict[str, List[str]] = load_categories(config)
        remove_duplicated_categories(self.categories)

        self.inverted_categories = collections.defaultdict(list)
        for category, tokens in self.categories.items():
            for token in tokens:
                self.inverted_categories[token].append(category)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        tokens_synsets = [self.get_similar(token) for token in tokens]

        synset_lengths = [len(synset.keys()) for synset in tokens_synsets]
        combinations = reduce((lambda x, y: x * y), synset_lengths)
        logger.debug(f'CategoriesGenerator synsets lengths: {synset_lengths} gives {combinations}')
        logger.debug(
            f'CategoriesGenerator synsets: {[list(synset.keys())[:100] for synset in tokens_synsets]}')

        result = []
        for synset_tuple in itertools.product(*[lemmas.items() for lemmas in tokens_synsets]):
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
