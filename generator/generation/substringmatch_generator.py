from operator import itemgetter
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

CACHE_TREE_PATH = 'data/cache/substringmatchgenerator_tree.bin_'
CACHE_TREE_HASH_PATH = 'data/cache/substringmatchgenerator_tree_hash.txt_'


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
        self.lines = list([x[0] for x in sorted(self.domains.taken.items(), key=itemgetter(1), reverse=True)])
        latest_hash = hashlib.sha256('\n'.join(self.lines).encode('utf-8')).hexdigest()

        domains_hash = hashlib.sha256(config.app.domains.encode('utf-8')).hexdigest()
        cache_tree_hash_path = CACHE_TREE_HASH_PATH + domains_hash
        cache_tree_path = CACHE_TREE_PATH + domains_hash
        cached_hash = None
        try:
            with open(cache_tree_hash_path, 'r') as f:
                cached_hash = f.read().strip()
        except FileNotFoundError:
            pass

        if cached_hash != latest_hash:
            self.tree = UniSuffixTree(self.lines)
            os.makedirs(os.path.dirname(cache_tree_path), exist_ok=True)
            os.makedirs(os.path.dirname(cache_tree_hash_path), exist_ok=True)
            self.tree.serialize(cache_tree_path)
            with open(cache_tree_hash_path, 'w') as f:
                f.write(latest_hash + '\n')
        else:
            self.tree = UniSuffixTree()
            # this is quite slow (over 2s)
            self.tree.deserialize(cache_tree_path)

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
        if len(''.join(tokens)) == 0:
            return []

        pattern = ''.join(tokens)

        if len(pattern) <= self.short_heuristic or self.suffix_tree_impl is None:
            names = self.re_impl.find(pattern)
        else:
            names = self.suffix_tree_impl.find(pattern)
        # self.limit=100 #TODO set to request's max_suggestions
        # return single tokens
        return ((name,) for name in islice(names, self.limit))

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return roundrobin(self.generate(name.strip_eth_namehash_unicode_long_name),
                          self.generate(name.strip_eth_namehash_long_name))
        # TODO: optimize

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_long_name, name.strip_eth_namehash_long_name)}
