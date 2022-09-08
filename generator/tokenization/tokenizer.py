from typing import List, Tuple

from generator.generated_name import GeneratedName


class Tokenizer:

    def __init__(self):
        pass

    def apply(self, tokenized_names: List[GeneratedName]) -> List[GeneratedName]:
        return [
            GeneratedName(
                subtokens,
                pipeline_name=name.pipeline_name,
                applied_strategies=[sublist + [self.__class__.__name__] for sublist in name.applied_strategies]
            )
            for name in tokenized_names
            for token in name.tokens
            for subtokens in self.tokenize(token)
        ]

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        raise NotImplementedError
