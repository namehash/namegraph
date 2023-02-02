from typing import List, Dict, Iterator

from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName


class RoundRobinSorter(Sorter):
    def sort(self,
             pipelines_suggestions: List[List[GeneratedName]],
             min_suggestions: int = None,
             max_suggestions: int = None,
             min_available_fraction: float = None) -> List[GeneratedName]:

        min_suggestions = min_suggestions or self.default_suggestions_count
        max_suggestions = max_suggestions or self.default_suggestions_count
        min_available_fraction = min_available_fraction or self.default_min_available_fraction

        used: Dict[str, GeneratedName] = dict()
        iters: List[Iterator[GeneratedName]] = [iter(l) for l in pipelines_suggestions]

        while True:
            all_empty = True
            for i in iters:
                while True:
                    # TODO we can remove try/except if we do not expect any Nones in the pipeline results
                    try:
                        x = next(i)
                        if x is None:
                            continue

                        if str(x) in used:
                            used[str(x)].add_strategies(x.applied_strategies)
                        else:
                            all_empty = False
                            used[str(x)] = x
                            break

                    except StopIteration:
                        break

            if all_empty: break

        suggestions = list(used.values())
        return self.satisfy_available_fraction_obligation(suggestions,
                                                          min_suggestions,
                                                          max_suggestions,
                                                          min_available_fraction)


