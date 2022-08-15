from typing import List, Tuple, Iterable
import re
from itertools import islice
import hashlib
import os

from generator.xgenerator import uniq

try:
    from suffixtree import SuffixQueryTree

    HAS_SUFFIX_TREE = True
except Exception:
    HAS_SUFFIX_TREE = False

from .name_generator import NameGenerator

CACHE_TREE_PATH = 'data/cache/substringmatchgenerator_tree.bin'
CACHE_TREE_HASH_PATH = 'data/cache/substringmatchgenerator_tree_hash.txt'


def _load_lines(path: str) -> List[str]:
    '''
    Load unique lines from file, removing .eth suffix.
    '''
    with open(path, 'r') as f:
        # return list(set([line.strip().removesuffix('.eth') for line in f.readlines()]))
        return uniq([line.strip().removesuffix('.eth') for line in f.readlines()])


class ReImpl:
    def __init__(self, config):
        lines = _load_lines(config.app.domains)
        self.data = '\n' + '\n'.join(lines) + '\n'

    def find(self, pattern: str) -> Iterable[str]:
        # strip \n from match
        return (name.group()[1:] for name in re.finditer(f'\n.*{re.escape(pattern)}.*', self.data))


class SuffixTreeImpl:
    def __init__(self, config):
        self.lines = _load_lines(config.app.domains)
        latest_hash = hashlib.sha256('\n'.join(self.lines).encode('utf-8')).hexdigest()

        cached_hash = None
        try:
            with open(CACHE_TREE_HASH_PATH, 'r') as f:
                cached_hash = f.read().strip()
        except FileNotFoundError:
            pass

        if cached_hash != latest_hash:
            self.tree = SuffixQueryTree(False, self.lines)
            os.makedirs(os.path.dirname(CACHE_TREE_PATH), exist_ok=True)
            os.makedirs(os.path.dirname(CACHE_TREE_HASH_PATH), exist_ok=True)
            self.tree.serialize(CACHE_TREE_PATH)
            with open(CACHE_TREE_HASH_PATH, 'w') as f:
                f.write(latest_hash + '\n')
        else:
            self.tree = SuffixQueryTree(False)
            # this is quite slow (over 2s)
            self.tree.deserialize(CACHE_TREE_PATH)

    def find(self, pattern: str) -> Iterable[str]:
        inds = self.tree.findStringIdx(pattern)
        return (self.lines[i] for i in inds)


class SubstringMatchGenerator(NameGenerator):
    def __init__(self, config):
        super().__init__()
        self.limit = config.generation.limit
        self.short_heuristic = 1
        self.suffix_tree_impl = SuffixTreeImpl(config) if HAS_SUFFIX_TREE else None
        self.re_impl = ReImpl(config)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        pattern = ''.join(tokens)

        if len(pattern) <= self.short_heuristic or self.suffix_tree_impl is None:
            names = self.re_impl.find(pattern)
        else:
            names = self.suffix_tree_impl.find(pattern)

        # return single tokens
        return [(name,) for name in islice(names, self.limit)]
