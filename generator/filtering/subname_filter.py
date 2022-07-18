import re
from pathlib import Path
from typing import Iterable, Set, List


class SubnameFilter:
    def __init__(self, config):
        subnames: Set[str] = set()
        with open(Path(config.filtering.root_path) / config.filtering.subnames) as subname_file:
            for line in subname_file:
                subnames.add(line.strip())
        self.pattern = re.compile('|'.join([re.escape(token) for token in subnames]))

    def apply(self, names: Iterable[str]) -> List[str]:
        return [n for n in names if not self.pattern.search(n)]
