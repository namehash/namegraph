from typing import List

from generator.generated_name import GeneratedName


class Normalizer:

    def __init__(self):
        pass

    def apply(self, tokenized_names: List[GeneratedName]) -> List[GeneratedName]:
        return [
            GeneratedName(
                tuple(self.normalize(token) for token in name.tokens),
                pipeline_name=name.pipeline_name,
                applied_strategies=[sublist + [self.__class__.__name__] for sublist in name.applied_strategies]
            )
            for name in tokenized_names
        ]

    def normalize(self, name: str) -> str:
        raise NotImplementedError
