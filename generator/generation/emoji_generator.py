import logging
import json
import math
from typing import List, Tuple, Any
from itertools import product, islice

from omegaconf import DictConfig

from .combination_limiter import CombinationLimiter
from .name_generator import NameGenerator
from ..the_name import TheName, Interpretation

logger = logging.getLogger('generator')


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


class EmojiGenerator(NameGenerator):
    """
    Replaces words with their corresponding emojis
    """

    def __init__(self, config: DictConfig):
        super().__init__(config)

        with open(config.generation.name2emoji_path, 'r', encoding='utf-8') as f:
            self.name2emoji = json.load(f)

        self.combination_limiter = CombinationLimiter(self.limit)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        all_possibilities = [self.name2emoji.get(token, []) + [token] for token in tokens]

        # skipping the name with all the original tokens
        diverse_results = list(islice(zip_longest_repeat_last(*all_possibilities), self.limit))
        diverse_results_set = set(diverse_results)

        all_possibilities_count = math.prod(map(len, all_possibilities))
        all_possibilities = self.combination_limiter.limit(all_possibilities)
        all_results = list(islice(order_product(*all_possibilities), min(self.limit, all_possibilities_count - 1)))

        return (diverse_results + [result for result in all_results if result not in diverse_results_set])[:self.limit]

    def generate2(self, name: TheName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: TheName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
