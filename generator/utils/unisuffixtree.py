from typing import Optional
from suffixtree import SuffixQueryTree
from generator.utils import unicode_wrap


# not inheriting to block the use of other methods


class UniSuffixTree:
    def __init__(self, lines: Optional[list[str]] = None):
        if lines is not None:
            self._tree = SuffixQueryTree(False, [unicode_wrap(line) for line in lines])
        else:
            self._tree = SuffixQueryTree(False)

    def findStringIdx(self, string: str) -> list[int]:
        return self._tree.findStringIdx(unicode_wrap(string))

    def serialize(self, path: str):
        self._tree.serialize(path)

    def deserialize(self, path: str):
        self._tree.deserialize(path)
