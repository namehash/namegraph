from typing import List, Dict, Iterator

from omegaconf import DictConfig

from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName


class RoundRobinSorter(Sorter):
    def sort(self, pipelines_suggestions: List[List[GeneratedName]]) -> List[GeneratedName]:
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

        return list(used.values())
