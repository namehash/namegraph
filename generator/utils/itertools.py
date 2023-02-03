from typing import Iterable, List, Dict


def sort_by_value(items: Iterable[str], scores: Dict[str, float], reverse: bool = False) -> List[str]:
    return sorted(items, key=lambda x: scores.get(x, 0.0), reverse=reverse)
