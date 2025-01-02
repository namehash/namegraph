from typing import List, Tuple, Optional, Any

from name_graph.generated_name import GeneratedName


class Tokenizer:

    def __init__(self):
        pass

    def apply(
            self,
            tokenized_names: List[GeneratedName],
            params: Optional[dict[str, Any]] = None
    ) -> List[GeneratedName]:
        return [
            GeneratedName(
                subtokens,
                pipeline_name=name.pipeline_name,
                applied_strategies=[sublist + [self.__class__.__name__] for sublist in name.applied_strategies],
                grouping_category=name.grouping_category
            )
            for name in tokenized_names
            for token in name.tokens
            for subtokens in self.tokenize(token)
        ]

    # todo add params argument here and for all tokenizers when needed
    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        raise NotImplementedError
