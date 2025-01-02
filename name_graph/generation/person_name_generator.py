import collections
import json
from operator import itemgetter
from typing import List, Tuple, Any, Optional

import numpy as np

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation
from name_graph.thread_utils import get_numpy_rng


def standardize(a):
    a = a + 1
    return a / np.sum(a)


class PersonNameGenerator(NameGenerator):
    """
    Person name generator that uses affixes.
    """

    def __init__(self, config):
        super().__init__(config)
        self.affixes = json.load(open(config.generation.person_name_affixes_path))
        self._prepare_affixes(self.affixes)

    def _prepare_affixes(self, affixes: dict[dict[str, int]]) -> None:
        self.male = collections.defaultdict(int)
        self.female = collections.defaultdict(int)
        self.both = collections.defaultdict(int)

        for key, d in affixes.items():
            for affix, count in d.items():
                if key == 'm_prefixes':
                    self.both[(affix, 'prefix')] += count
                    self.male[(affix, 'prefix')] += count
                elif key == 'f_prefixes':
                    self.both[(affix, 'prefix')] += count
                    self.female[(affix, 'prefix')] += count
                elif key == 'm_suffixes':
                    self.both[(affix, 'suffix')] += count
                    self.male[(affix, 'suffix')] += count
                elif key == 'f_suffixes':
                    self.both[(affix, 'suffix')] += count
                    self.female[(affix, 'suffix')] += count

        self.male = (list(self.male.keys()), standardize(np.array(list(self.male.values()))))
        self.female = (list(self.female.keys()), standardize(np.array(list(self.female.values()))))
        self.both = (list(self.both.keys()), standardize(np.array(list(self.both.values()))))

    def generate(self, tokens: Tuple[str, ...], gender: str = None) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        if gender == 'M':
            data = self.male
        elif gender == 'F':
            data = self.female
        else:
            data = self.both

        order = get_numpy_rng().choice(len(data[0]), size=len(data[0]), replace=False, p=data[1])
        return (tokens + (data[0][index][0],) if data[0][index][1] == 'suffix' else (data[0][index][0],) + tokens for
                index in order)

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        try:
            gender = max(interpretation.features['gender'].items(), key=itemgetter(1))[0]
        except:
            gender = None
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid,), 'gender': gender}

    def get_grouping_category(self, output_name: Optional[str] = None):
        if self._grouping_category == 'dynamic_' and output_name is not None:
            return 'expand' if output_name.isascii() else 'emojify'
        elif self._grouping_category == 'dynamic_':
            return 'expand'
        return self._grouping_category
