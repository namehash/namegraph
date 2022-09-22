from typing import List

from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName
from generator.utils import aggregate_duplicates


class CountSorter(Sorter):
    def sort(self,
             pipelines_suggestions: List[List[GeneratedName]],
             min_suggestions: int = None,
             max_suggestions: int = None) -> List[GeneratedName]:

        min_suggestions = min_suggestions or self.config.app.suggestions
        max_suggestions = max_suggestions or self.config.app.suggestions

        flattened = [x for sublist in pipelines_suggestions for x in sublist]
        aggregated = aggregate_duplicates(flattened)

        suggestions = [x for x in sorted(aggregated, key=lambda x: len(x.applied_strategies), reverse=True)]
        return self.satisfy_primary_fraction_obligation(suggestions, min_suggestions, max_suggestions)
