from typing import Iterable, List, Dict
from collections import defaultdict


def sort_by_value(items: Iterable[str], scores: Dict[str, float], reverse: bool = False) -> List[str]:
    scores = defaultdict(float, scores)
    return sorted(items, key=scores.get, reverse=reverse)
