from typing import List

from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName
from generator.utils import aggregate_duplicates


class CountSorter(Sorter):
    def sort(self, pipelines_suggestions: List[List[GeneratedName]]) -> List[GeneratedName]:
        flattened = [x for sublist in pipelines_suggestions for x in sublist]
        aggregated = aggregate_duplicates(flattened)

        return [x for x in sorted(aggregated, key=lambda x: len(x.applied_strategies), reverse=True)]
