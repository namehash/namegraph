import re


class ValidNameFilter:
    def __init__(self, config):
        pass

    def apply(self, names):
        return [n for n in names if len(n) >= 3 and re.match(r'^[a-z0-9-]+$', n)]
