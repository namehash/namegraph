from copy import copy
from typing import List, Dict, Iterator

from omegaconf import DictConfig


from generator.sorting.sorter import Sorter
from generator.generated_name import GeneratedName
from generator.the_name import Interpretation, TheName


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


class RoundRobinSorter2(Sorter):
    def __init__(self, config: DictConfig, pipelines):
        super().__init__(config)
        self.used_pipelines = set()
        self.pipelines = copy(pipelines)
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        # print('Robin', self.index , len(self.pipelines), self, [p.definition.name for p in self.pipelines])
        if self.index < len(self.pipelines):
            pipeline = self.pipelines[self.index]
            self.index = (self.index + 1) % len(self.pipelines)
            return pipeline
        raise StopIteration
        
        # while True:
        # 
        #     for pipeline in self.pipelines:
        #         if pipeline not in self.used_pipelines:
        #             return pipeline
        #     if len(self.pipelines) == len(self.used_pipelines):  # TODO: optimize
        #         break
                # raise StopIteration

    # def next_suggestion(self, name: TheName, interpretation: Interpretation):
    #     while True:
    #         for pipeline in self.pipelines:
    #             yield pipeline

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

    def pipeline_used(self, sampled_pipeline):
        # self.used_pipelines.add(sampled_pipeline)
        self.pipelines.remove(sampled_pipeline)
        if len(self.pipelines):
            self.index = self.index % len(self.pipelines)
        
