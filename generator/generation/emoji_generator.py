import logging
import json
from typing import List, Tuple, Any
from itertools import product, islice

from omegaconf import DictConfig

from .combination_limiter import CombinationLimiter
from .name_generator import NameGenerator

logger = logging.getLogger('generator')


def order_product(*args):
    return [tuple(i[1] for i in p) for p in
            sorted(product(*map(enumerate, args)),
                   key=lambda x: (sum(y[0] for y in x), x))]


class EmojiGenerator(NameGenerator):
    """
    Replaces words with their corresponding emojis
    """

    def __init__(self, config: DictConfig):
        super().__init__(config)

        with open(config.generation.name2emoji_path, 'r', encoding='utf-8') as f:
            self.name2emoji = json.load(f)

        self.combination_limiter = CombinationLimiter(self.limit)

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        all_possibilities = [[token] + self.name2emoji.get(token, []) for token in tokens]

        all_possibilities = self.combination_limiter.limit(all_possibilities)

        # skipping the item in which all the original tokens are preserved
        return list(islice(order_product(*all_possibilities), 1, self.limit))
