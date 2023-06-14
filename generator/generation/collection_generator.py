import logging
from typing import List, Tuple, Iterable, Any
from itertools import cycle, islice

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation
from ..collection import CollectionMatcher
from ..generated_name import GeneratedName

logger = logging.getLogger('generator')


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))


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
        collections, _ = self.collection_matcher.search_for_generator(
            tokens,
            max_related_collections=self.collections_limit,
        )

        for collection in collections:
            logger.info(f'Collection: {collection.title} score: {collection.score} names: {len(collection.names)}')

        # list of collections, where each collection is a list of tuples - (collection object, tokenized_name)
        collections_with_tuples = [
            [(collection, tokenized_name) for tokenized_name in collection.tokenized_names[:self.suggestions_limit]]
            for collection in collections
        ]

        return (
            GeneratedName(tokenized_name, applied_strategies=[[self.__class__.__name__]], collection=collection.title)
            for collection, tokenized_name in roundrobin(*collections_with_tuples)
            if tokenized_name != tokens
        )

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        collections, _ = self.collection_matcher.search_for_generator(
            tokens,
            max_related_collections=self.collections_limit,
        )
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
