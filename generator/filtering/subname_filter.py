from pathlib import Path
from typing import Iterable, Set


class SubnameFilter:
    def __init__(self, config):
        self.subnames: Set[str] = set()
        with open(Path(config.filtering.root_path) / config.filtering.subnames) as subname_file:
            for line in subname_file:
                self.subnames.add(line.strip())

    def apply(self, names: Iterable[str]):
        return [n for n in names if all([subname not in n for subname in self.subnames])]
