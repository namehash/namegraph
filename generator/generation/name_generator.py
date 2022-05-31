from typing import List, Dict

class GeneratedName:
    def __init__(self, tokens: List[str], applied_strategies=None):
        self.tokens = tokens
        if applied_strategies is None:
            self.applied_strategies = []
        else:
            self.applied_strategies = applied_strategies  # history of applied strategies

    def __str__(self):
        return ''.join(self.tokens)

class NameGenerator:
    def __init__(self):
        pass

    def apply(self, tokenized_name: GeneratedName) -> List[GeneratedName]:
        return [GeneratedName(changed, tokenized_name.applied_strategies + [self.__class__.__name__]) for changed in
                self.generate(tokenized_name.tokens)]

    def generate(self, tokens: List[str]) -> List[List[str]]:
        pass
