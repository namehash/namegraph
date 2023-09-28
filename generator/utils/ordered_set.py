from collections import OrderedDict


class OrderedSet(set):
    def __init__(self, iterable=None):
        super().__init__()
        self._ordered_dict = OrderedDict.fromkeys(iterable) if iterable is not None else OrderedDict()

    def add(self, element):
        self._ordered_dict[element] = None

    def update(self, iterable):
        for element in iterable:
            self.add(element)

    def remove(self, element):
        del self._ordered_dict[element]

    def __contains__(self, element):
        return element in self._ordered_dict

    def __iter__(self):
        return iter(self._ordered_dict.keys())

    def __len__(self):
        return len(self._ordered_dict)

    def __eq__(self, other):
        return isinstance(other, OrderedSet) and self._ordered_dict == other._ordered_dict

    def __copy__(self):
        return OrderedSet(self._ordered_dict.keys())

    def __repr__(self):
        return f"OrderedSet({list(self._ordered_dict.keys())})"
