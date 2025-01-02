import logging
import math
from typing import List, Tuple, Any
from itertools import product, islice

from more_itertools import collapse
from omegaconf import DictConfig

from .combination_limiter import CombinationLimiter
from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation

logger = logging.getLogger('name_graph')


def zip_longest_repeat_last(*lists):
    max_length = max([len(list_) for list_ in lists], default=0)
    # skipping the last one with all original tokens
    for i in range(max_length - 1):
        yield tuple([
            list_[i] if i < len(list_) else list_[-1]
            for list_ in lists
        ])


def order_product(*args):
    return [
        tuple(i[1] for i in p)
        for p in sorted(product(*map(enumerate, args)),
                        key=lambda x: (sum(y[0] for y in x), x))
    ]


class CharacterGenerator(NameGenerator):
    """
    Replaces words with their corresponding characters
    """

    def __init__(self, config: DictConfig):
        super().__init__(config)
        self.combination_limiter = CombinationLimiter(self.limit)

    def get_all_possibilities(self, tokens: Tuple[str, ...]) -> List[List[str]]:
        raise NotImplementedError('this is an abstract class with no mapping specified')

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        all_possibilities = self.get_all_possibilities(tokens)

        if len(tokens) == 1:
            return [(tokens[0], possibility) for possibility in all_possibilities[0][:-1]]

        if len(tokens) == 2:
            first_token_substitutions = [(possibility, tokens[1]) for possibility in all_possibilities[0][:-1]]
            second_token_substitutions = [(tokens[0], possibility) for possibility in all_possibilities[1][:-1]]
            min_length = min(len(first_token_substitutions), len(second_token_substitutions))
            return list(collapse(zip(first_token_substitutions, second_token_substitutions), levels=1)) \
                + first_token_substitutions[min_length:] + second_token_substitutions[min_length:]

        # skipping the name with all the original tokens
        diverse_results = list(islice(zip_longest_repeat_last(*all_possibilities), self.limit))
        diverse_results_set = set(diverse_results)

        all_possibilities_count = math.prod(map(len, all_possibilities))
        all_possibilities = self.combination_limiter.limit(all_possibilities)
        all_results = list(islice(order_product(*all_possibilities), min(self.limit, all_possibilities_count - 1)))

        return (diverse_results + [result for result in all_results if result not in diverse_results_set])[:self.limit]

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
