from typing import Any
import json
import regex as re

from .name_generator import NameGenerator


LEETSPEAK_PATH = 'data/leetspeak.json'


class LeetGenerator(NameGenerator):
    def __init__(self, config):
        super().__init__()

        with open(LEETSPEAK_PATH) as f:
            self._leetspeak = json.load(f)

        # has to match entire token
        sequences = '(?:^(' + '|'.join(re.escape(s) for s in sorted(self._leetspeak['sequences'].keys(), key=len, reverse=True)) + ')$)'

        # matches single characters
        letters = '(' + '|'.join(re.escape(s) for s in self._leetspeak['letters'].keys()) + ')'

        self._pat = re.compile(rf'{sequences}|{letters}', re.IGNORECASE)

    def _leet_repl(self, m: re.Match) -> str:
        if m.group(1) is not None:
            return self._leetspeak['sequences'][m.group(1).lower()][0]
        
        if m.group(2) is not None:
            return self._leetspeak['letters'][m.group(2).lower()][0]
        
        return m.group(0)

    def _leetify(self, tokens: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(self._pat.sub(self._leet_repl, t) for t in tokens)

    def generate(self, tokens: tuple[str, ...], params: dict[str, Any]) -> list[tuple[str, ...]]:
        return [self._leetify(tokens)]
