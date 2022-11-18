import logging
import json
from typing import List, Tuple, Any
from itertools import product, islice

from omegaconf import DictConfig

from .name_generator import NameGenerator

logger = logging.getLogger('generator')


class EmojiGenerator(NameGenerator):
    """
    Replaces words with their corresponding emojis
    """

    def __init__(self, config: DictConfig):
        super().__init__(config)

        with open(config.generation.name2emoji_path, 'r', encoding='utf-8') as f:
            self.name2emoji = json.load(f)

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        all_possibilities = [[token] + self.name2emoji.get(token, []) for token in tokens]
        # skipping the item in which all the original tokens are preserved
        return list(islice(product(*all_possibilities), 1, self.limit))
