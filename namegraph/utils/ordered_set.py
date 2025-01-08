from collections import OrderedDict
from collections.abc import MutableSet


class OrderedSet(MutableSet):
    def __init__(self, iterable=None):
        super().__init__()
        self._ordered_dict = OrderedDict.fromkeys(iterable) if iterable is not None else OrderedDict()

    def discard(self, value) -> None:
        if value in self._ordered_dict:
            del self._ordered_dict[value]

    def remove(self, element):
        del self._ordered_dict[element]

    def add(self, element):
        self._ordered_dict[element] = None

    def __contains__(self, element):
        return element in self._ordered_dict

    def __iter__(self):
        return iter(self._ordered_dict.keys())

    def __len__(self):
        return len(self._ordered_dict)

    def __eq__(self, other):
        return isinstance(other, OrderedSet) and self._ordered_dict == other._ordered_dict

    def __repr__(self):
        return f"OrderedSet({list(self._ordered_dict.keys())})"
