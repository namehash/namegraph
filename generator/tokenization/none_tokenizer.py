from typing import List, Tuple


class NoneTokenizer():
    """Return the input withopout tokenization."""

    def __init__(self, config):
        pass

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        return [(name,)]
