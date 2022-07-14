import json
from typing import Iterable, Any, Union

import regex
from omegaconf import DictConfig


class Confusables:
    """https://www.unicode.org/Public/security/latest/confusablesSummary.txt"""

    def __init__(self, config: DictConfig):
        self.config = config
        self.confusable_chars = json.load(open(config.inspector.confusables))

    def is_confusable(self, character) -> bool:
        if regex.match(r'[a-z0-9-]', character):
            return False
        return character in self.confusable_chars

    def get_confusables(self, character) -> Iterable[str]:
        if self.is_confusable(character):
            return self.confusable_chars[character]
        else:
            return ()

    def get_canonical(self, character) -> Union[Any, None]:
        if self.is_confusable(character):
            return self.confusable_chars[character][0]
        else:
            return None

    def analyze(self, character):
        return self.is_confusable(character), self.get_confusables(character)
