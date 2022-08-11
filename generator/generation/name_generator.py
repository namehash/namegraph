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

    def apply(self, tokenized_name: GeneratedName) -> List[GeneratedName]:
        return [GeneratedName(changed, tokenized_name.applied_strategies + [self.__class__.__name__]) for changed in
                self.generate(tokenized_name.tokens)]

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        raise NotImplementedError
