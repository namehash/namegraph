from typing import List, Tuple, Iterable, Any

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation
from ..collection import CollectionMatcher
from ..generated_name import GeneratedName


class CollectionGenerator(NameGenerator):
    """
    Searches for the collection given the entry name, and then yields other names from the collections
    """

    def __init__(self, config):
        super().__init__(config)
        self.collection_matcher = CollectionMatcher(config)
        self.collections_limit = config.collections.collections_limit
        self.suggestions_limit = config.collections.suggestions_limit

    def apply(self, name: InputName, interpretation: Interpretation) -> Iterable[GeneratedName]:
        tokens = interpretation.tokenization
        collections = self.collection_matcher.search(tokens, tokenized=True, limit=self.collections_limit)

        return (
            GeneratedName(name_tokens, applied_strategies=[[self.__class__.__name__]], collection=collection.title)
            for collection in collections
            for name_tokens in collection.tokenized_names[:self.suggestions_limit]
            if name_tokens != tokens
        )

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        collections = self.collection_matcher.search(tokens, tokenized=True, limit=self.collections_limit)
        # TODO round robin? weighted sampling?
        return [
            name_tokens
            for collection in collections
            for name_tokens in collection.tokenized_names[:self.suggestions_limit]
            if name_tokens != tokens
        ]

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
