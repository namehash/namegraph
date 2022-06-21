from typing import Tuple


class GeneratedName:
    __slots__ = ['tokens', 'applied_strategies']

    def __init__(self, tokens: Tuple[str, ...], applied_strategies=None):
        self.tokens = tokens
        if applied_strategies is None:
            self.applied_strategies = []
        else:
            self.applied_strategies = applied_strategies  # history of applied strategies

    def __str__(self):
        return ''.join(self.tokens)

    def __repr__(self):
        return self.__str__()

    def __json__(self):
        return ''.join(self.tokens)
