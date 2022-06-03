from pathlib import Path
from typing import Iterable, Set


class DomainFilter:
    def __init__(self, config):
        self.domains: Set[str] = set()
        with open(Path(config.filtering.root_path) / config.filtering.domains) as domains_file:
            for line in domains_file:
                self.domains.add(line.strip()[:-4])

    def apply(self, names: Iterable[str]):
        return [n for n in names if n not in self.domains]
