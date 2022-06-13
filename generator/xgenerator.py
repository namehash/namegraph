from itertools import zip_longest, chain, repeat
from multiprocessing import Pool
from typing import List

from generator.pipeline import Pipeline
from omegaconf import DictConfig


def by_one_iterator(lists):
    return [x for x in chain(*zip_longest(*lists)) if x is not None]


class Generator():
    def __init__(self, config: DictConfig):
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            self.pipelines.append(Pipeline(definition, self.config))

    def generate_names(self, name: str, count: int) -> List[str]:
        suggestions = []

        multiprocessing=self.config.app.use_multiprocessing
        if multiprocessing:
            with Pool(8) as pool:
                tasks = zip([pipeline.apply for pipeline in self.pipelines], repeat([name]))
                futures = [pool.apply_async(*t) for t in tasks]
                results = [fut.get() for fut in futures]
                suggestions=results
        else:
            for pipeline in self.pipelines:
                pipeline_suggestions = pipeline.apply(name)
                suggestions.append(pipeline_suggestions)

        combined_suggestions = list(by_one_iterator(suggestions))
        # TODO uniq

        return combined_suggestions[:count]
