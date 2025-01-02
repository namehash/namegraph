import logging
import json
from typing import List, Tuple

from omegaconf import DictConfig

from .character_generator import CharacterGenerator

logger = logging.getLogger('name_graph')


class SymbolGenerator(CharacterGenerator):
    """
    Replaces words with their corresponding symbols
    """

    def __init__(self, config: DictConfig):
        super().__init__(config)

        with open(config.generation.name2symbol_path, 'r', encoding='utf-8') as f:
            self.name2symbol = json.load(f)

    def get_all_possibilities(self, tokens: Tuple[str, ...]) -> List[List[str]]:
        return [self.name2symbol.get(token, []) + [token] for token in tokens]
