import re

from .filter import Filter


class ValidNameLengthFilter(Filter):
    def __init__(self, config):
        super().__init__()

    def filter_name(self, name: str) -> bool:
        return len(name) >= 3
