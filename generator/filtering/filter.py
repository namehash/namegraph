from typing import List, Iterable, Any, Optional

from generator.generated_name import GeneratedName


class Filter:

    def __init__(self):
        pass

    def apply(
            self,
            tokenized_names: List[GeneratedName],
            params: Optional[dict[str, Any]] = None
    ) -> List[GeneratedName]:

        result = [tokenized_name for tokenized_name in tokenized_names if self.filter_name(str(tokenized_name))]
        for name in result:
            name.append_strategy_point(self.__class__.__name__)
        return result

    # todo add params argument here and for all filters when needed
    def filter_name(self, name: str) -> bool:
        raise NotImplementedError
