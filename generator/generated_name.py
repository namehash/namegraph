from typing import Tuple, List, Optional


class GeneratedName:
    __slots__ = ['tokens', 'pipeline_name', 'category', 'applied_strategies']

    def __init__(self,
                 tokens: Tuple[str, ...],
                 pipeline_name: Optional[str] = None,
                 category: Optional[str] = None,
                 applied_strategies: Optional[List[List[str]]] = None):

        self.tokens = tokens

        self.pipeline_name = pipeline_name
        self.category = category
        self.applied_strategies = []  # history of applied strategies

        if applied_strategies is not None:
            self.add_strategies(applied_strategies)
        else:
            self.applied_strategies.append([])

    def __str__(self):
        return ''.join(self.tokens)

    def __repr__(self):
        return str(self.tokens)

    def __json__(self):
        return ''.join(self.tokens)

    def add_strategies(self, strategies: List[List[str]]) -> None:
        for strategy in strategies:
            if strategy not in self.applied_strategies:
                self.applied_strategies.append(strategy)

    def append_strategy_point(self, point: str) -> None:
        # we do not need any duplicates checking, as adding same value to unique values keeps them unique
        for strategy in self.applied_strategies:
            strategy.append(point)
