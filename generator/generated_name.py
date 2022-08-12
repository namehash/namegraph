from typing import Tuple, List, Optional


class GeneratedName:
    __slots__ = ['tokens', 'applied_strategies']

    def __init__(self, tokens: Tuple[str, ...], applied_strategies: Optional[List[List[str]]] = None):
        self.tokens = tokens
        self.applied_strategies = applied_strategies or [[]]  # history of applied strategies

    def __str__(self):
        return ''.join(self.tokens)

    def __repr__(self):
        return str(self.tokens)

    def __json__(self):
        return ''.join(self.tokens)
