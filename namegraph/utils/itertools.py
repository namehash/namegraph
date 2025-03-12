from typing import Iterable, Hashable


def sort_by_value(items: Iterable[Hashable], scores: dict[Hashable, float], reverse: bool = False) -> list[Hashable]:
    return sorted(items, key=lambda x: scores.get(x, 0.0), reverse=reverse)


def sort_by_value_under_key(
        items: Iterable[Iterable | dict],
        scores: dict[Hashable, float],
        sort_key: str | int,
        reverse: bool = False
) -> list[Iterable | dict]:
    return sorted(items, key=lambda x: scores.get(x[sort_key], 0.0), reverse=reverse)
