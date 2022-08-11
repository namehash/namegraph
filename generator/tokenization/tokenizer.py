from typing import List, Tuple

from generator.generated_name import GeneratedName


class Tokenizer:

    def __init__(self):
        pass

    def apply(self, tokenized_name: GeneratedName) -> List[GeneratedName]:
        return [GeneratedName(changed, tokenized_name.applied_strategies + [self.__class__.__name__]) for changed in
                self.tokenize(tokenized_name.tokens[0])]

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        raise NotImplementedError
