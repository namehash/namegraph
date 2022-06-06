from functools import reduce
from typing import List


def prod(l: List[int]):
    if not l: return 1
    return reduce((lambda x, y: x * y), l)


def prod_with_indexes(counts_with_indexes: List[List[int]]):
    return prod([x[0] for x in counts_with_indexes])


class CombinationLimiter:
    """Limits number of combinations."""

    def __init__(self, max_limit=10000):
        self.max_limit = max_limit

    def limit(self, l: List[List]):
        counts = [len(subl) for subl in l]
        new_counts = self.compute_limits(counts)
        return [subl[:limit] for subl, limit in zip(l, new_counts)]

    def compute_limits(self, counts: List[int]):
        # sort counts in decrease order and save indexes
        counts_with_indexes = sorted([[count, index] for index, count in enumerate(counts)], reverse=True)

        n = len(counts_with_indexes)
        for i in range(n):
            combinations = prod_with_indexes(counts_with_indexes)
            if combinations <= self.max_limit:
                break
            if i + 1 < n:
                new_count1 = counts_with_indexes[i + 1][0]
            else:
                new_count1 = 1
            new_count2 = int(self.max_limit ** (1 / n))
            new_count3 = int((self.max_limit / prod_with_indexes(counts_with_indexes[i + 1:])) ** (1 / (i + 1)))
            new_count = max(new_count1, new_count2, new_count3)

            # set new limit for i and previous counts
            for j in range(i + 1):
                counts_with_indexes[j][0] = new_count

        # increment limits separately
        for i in range(n):
            counts_with_indexes[i][0] += 1
            combinations = prod_with_indexes(counts_with_indexes)
            if combinations > self.max_limit:
                counts_with_indexes[i][0] -= 1
                break

        return [counts_with_index[0] for counts_with_index in sorted(counts_with_indexes, key=lambda x: x[1])]
