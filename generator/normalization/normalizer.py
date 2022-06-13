from generator.generated_name import GeneratedName


class Normalizer:

    def __init__(self):
        pass

    def apply(self, tokenized_name: GeneratedName) -> GeneratedName:
        return GeneratedName((self.normalize(tokenized_name.tokens[0]),), [self.__class__.__name__])

    def normalize(self, name: str) -> str:
        raise NotImplementedError
