import re
from .filter import Filter


class ValidNameFilter(Filter):
    def __init__(self, config):
        super().__init__()

    def filter_name(self, name: str) -> bool:
        return len(name) >= 3 and re.match(r'^[a-z0-9](-*[a-z0-9])+$', name)
