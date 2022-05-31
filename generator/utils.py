from typing import List


def uniq(list: List) -> List:
    used = set()
    return [x for x in list if x not in used and (used.add(x) or True)]
