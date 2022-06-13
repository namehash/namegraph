import re
from pathlib import Path
from typing import Iterable, Set
from .filter import Filter


class SubnameFilter(Filter):
    def __init__(self, config):
        super().__init__()
        subnames: Set[str] = set()
        with open(Path(config.filtering.root_path) / config.filtering.subnames) as subname_file:
            for line in subname_file:
                subnames.add(line.strip())
        self.pattern = re.compile('|'.join([re.escape(token) for token in subnames]))

    def filter_name(self, name: str) -> bool:
        return not self.pattern.search(name)