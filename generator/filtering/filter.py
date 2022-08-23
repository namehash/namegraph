from typing import List, Iterable

from generator.generated_name import GeneratedName


class Filter:

    def __init__(self):
        pass

    def apply(self, tokenized_names: List[GeneratedName]) -> List[GeneratedName]:
        result = []
        for tokenized_name in tokenized_names:
            if self.filter_name(str(tokenized_name)):
                result.append(tokenized_name)
                tokenized_name.append_strategy_point(self.__class__.__name__)

        return result

    def filter_name(self, name: str) -> bool:
        raise NotImplementedError
