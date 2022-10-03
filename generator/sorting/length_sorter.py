from typing import List

from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName
from generator.utils import aggregate_duplicates


class LengthSorter(Sorter):
    def sort(self,
             pipelines_suggestions: List[List[GeneratedName]],
             min_suggestions: int = None,
             max_suggestions: int = None,
             min_primary_fraction: float = None) -> List[GeneratedName]:

        min_suggestions = min_suggestions or self.default_suggestions_count
        max_suggestions = max_suggestions or self.default_suggestions_count
        min_primary_fraction = min_primary_fraction or self.default_min_primary_fraction

        flattened = [x for sublist in pipelines_suggestions for x in sublist]
        aggregated = aggregate_duplicates(flattened)

        suggestions = [x for x in sorted(aggregated, key=lambda y: len(str(y)), reverse=False)]
        return self.satisfy_primary_fraction_obligation(suggestions,
                                                        min_suggestions,
                                                        max_suggestions,
                                                        min_primary_fraction)
