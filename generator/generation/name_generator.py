from typing import List, Tuple

from generator.generated_name import GeneratedName


class NameGenerator:
    """
    Base class for generating names. The class is reposnsible for generating new
    names based on the already tokenized input. It provides the apply method,
    responsible for registering the applied generators.
    """

    def __init__(self):
        pass

    def apply(self, tokenized_names: List[GeneratedName]) -> List[GeneratedName]:
        return [
            GeneratedName(
                generated,
                [sublist + [self.__class__.__name__] for sublist in name.applied_strategies]
            )
            for name in tokenized_names
            for generated in self.generate(name.tokens)
        ]

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        raise NotImplementedError
