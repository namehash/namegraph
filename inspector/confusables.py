import json
from typing import Iterable, Any, Union, Dict, List

import regex
from omegaconf import DictConfig


class Confusables:
    """Stores confusable characters."""

    def __init__(self, config: DictConfig):
        self.config = config
        self.confusable_chars: Dict[str, List[str]] = json.load(open(config.inspector.confusables))

    def is_confusable(self, character: str) -> bool:
        if regex.match(r'[a-z0-9-]', character):
            return False
        return character in self.confusable_chars

    def get_confusables(self, character: str) -> Iterable[str]:
        if self.is_confusable(character):
            return self.confusable_chars[character]
        else:
            return ()

    def get_canonical(self, character: str) -> Union[Any, None]:
        if self.is_confusable(character):
            return self.confusable_chars[character][0]
        else:
            return None

    def analyze(self, character: str) -> (bool, Iterable[str]):
        return self.is_confusable(character), self.get_confusables(character)
