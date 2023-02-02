from typing import List, Tuple, Iterable, Dict, Any
from itertools import islice, cycle
import hashlib
import re
import os

from generator.utils.unisuffixtree import UniSuffixTree, HAS_SUFFIX_TREE

from .name_generator import NameGenerator
from ..domains import Domains
from ..input_name import Interpretation, InputName
from ..utils import sort_by_value

CACHE_TREE_PATH = 'data/cache/substringmatchgenerator_tree.bin'
CACHE_TREE_HASH_PATH = 'data/cache/substringmatchgenerator_tree_hash.txt'


class ReImpl:
    def __init__(self, config):
        self.domains = Domains(config)
        lines = sort_by_value(self.domains.taken.keys(), self.domains.taken, reverse=True)
        self.data = '\n' + '\n'.join(lines) + '\n'

    def find(self, pattern: str) -> Iterable[str]:
        # strip \n from match
        return (name.group()[1:] for name in re.finditer(f'\n.*{re.escape(pattern)}.*', self.data))


class SuffixTreeImpl:
    def __init__(self, config):
        self.domains = Domains(config)
        self.lines = list(self.domains.taken.keys())
        latest_hash = hashlib.sha256('\n'.join(self.lines).encode('utf-8')).hexdigest()

        cached_hash = None
        try:
            with open(CACHE_TREE_HASH_PATH, 'r') as f:
                cached_hash = f.read().strip()
        except FileNotFoundError:
            pass

        if cached_hash != latest_hash:
            self.tree = UniSuffixTree(self.lines)
            os.makedirs(os.path.dirname(CACHE_TREE_PATH), exist_ok=True)
            os.makedirs(os.path.dirname(CACHE_TREE_HASH_PATH), exist_ok=True)
            self.tree.serialize(CACHE_TREE_PATH)
            with open(CACHE_TREE_HASH_PATH, 'w') as f:
                f.write(latest_hash + '\n')
        else:
            self.tree = UniSuffixTree()
            # this is quite slow (over 2s)
            self.tree.deserialize(CACHE_TREE_PATH)

    def find(self, pattern: str) -> Iterable[str]:
        inds = self.tree.findStringIdx(pattern)
        return (self.lines[i] for i in inds)


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))


class SubstringMatchGenerator(NameGenerator):
    def __init__(self, config):
        super().__init__(config)
        self.domains = Domains(config)
        self.short_heuristic = 1
        self.suffix_tree_impl = SuffixTreeImpl(config) if HAS_SUFFIX_TREE else None
        self.re_impl = ReImpl(config)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        pattern = ''.join(tokens)

        if len(pattern) <= self.short_heuristic or self.suffix_tree_impl is None:
            names = self.re_impl.find(pattern)
        else:
            names = self.suffix_tree_impl.find(pattern)
            names = sort_by_value(islice(names, self.limit), self.domains.taken, reverse=True)

        # return single tokens
        return [(name,) for name in islice(names, self.limit)]

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return roundrobin(self.generate(name.strip_eth_namehash_unicode_long_name),
                          self.generate(name.strip_eth_namehash_long_name))
        # TODO: optimize

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_long_name, name.strip_eth_namehash_long_name)}
