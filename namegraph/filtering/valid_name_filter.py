import re

from .filter import Filter


class ValidNameFilter(Filter):
    def __init__(self, config):
        super().__init__()
        self.pattern = re.compile(r'^[a-z0-9_$](-*[a-z0-9])+$')

    def filter_name(self, name: str) -> bool:
        return len(name) >= 3 and self.pattern.match(name)
