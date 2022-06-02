from typing import List, Tuple


class GeneratedName:
    def __init__(self, tokens: List[str], applied_strategies=None):
        self.tokens = tokens
        if applied_strategies is None:
            self.applied_strategies = []
        else:
            self.applied_strategies = applied_strategies  # history of applied strategies

    def __str__(self):
        return ''.join(self.tokens)

    def __repr__(self):
        return self.__str__()

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
        pass
