import logging
from typing import List, Tuple, Iterable, Any
from itertools import cycle, islice

from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation
from ..xcollections import CollectionMatcherForGenerator
from ..generated_name import GeneratedName

logger = logging.getLogger('generator')


def uniq(l):
    used = set()
    return [x for x in l if x not in used and (used.add(x) or True)]


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
        self.collection_matcher = CollectionMatcherForGenerator(config)
        self.collections_limit = config.collections.collections_limit
        self.suggestions_limit = config.collections.suggestions_limit
        self.name_diversity_ratio = config.collections.name_diversity_ratio
        self.max_per_type = config.collections.max_per_type

    def apply(self, name: InputName, interpretation: Interpretation) -> Iterable[GeneratedName]:
        # TODO maybe use concatenation of all tokenizations as query
        input_name: str = name.strip_eth_namehash_unicode_long_name.strip()
        # if ' ' in name.strip_eth_namehash_unicode_long_name:  # todo: can it be removed?
        #     tokens = input_name.split(' ')
        if name.is_pretokenized:
            tokens = name.pretokenization
        else:
            # tokens = interpretation.tokenization
            # alternative 1
            # tokens = list(interpretation.tokenization) + [name.strip_eth_namehash_unicode_long_name.strip()]
            # alternative 2 all tokenizations
            tokens = []
            if input_name:
                tokens.append(input_name)
            for interpretations2 in name.interpretations.values():
                for interpretation in interpretations2:
                    # skip tokenizations with initials
                    if 'type' in interpretation.features and interpretation.features['type'] in (
                    'first with initial', 'last with initial'):
                        continue
                    tokens.extend(interpretation.tokenization)

            tokens = uniq(tokens)
            if input_name:
                tokens[0] = f'{tokens[0]}^1.5'  # boost untokenized

        params = name.params if name.params is not None else dict()
        suggestions_limit = max(params.get('max_names_per_related_collection', 0), self.suggestions_limit)
        logger.info(f'CollectionGenerator query: {tokens}')
        collections, _ = self.collection_matcher.search_for_generator(
            tuple(tokens),
            name.strip_eth_namehash_unicode_long_name.strip(),
            max_related_collections=params.get('max_related_collections', self.collections_limit),
            name_diversity_ratio=params.get('name_diversity_ratio', self.name_diversity_ratio),
            max_per_type=params.get('max_per_type', self.max_per_type),
            limit_names=suggestions_limit,
            enable_learning_to_rank=params.get('enable_learning_to_rank', True),
        )

        for collection in collections:
            logger.info(f'Collection: {collection.title} score: {collection.score} names: {len(collection.names)}')

        # list of collections, where each collection is a list of tuples - (collection object, tokenized_name)
        collections_with_tuples = [
            [(collection, tokenized_name) for tokenized_name in collection.tokenized_names[:suggestions_limit]]
            for collection in collections
        ]

        return (
            GeneratedName(tokenized_name,
                          applied_strategies=[[self.__class__.__name__]],
                          grouping_category=self.get_grouping_category(output_name=''.join(tokenized_name)),
                          collection_title=collection.title,
                          collection_id=collection.collection_id,
                          collection_members_count=collection.number_of_names,
                          related_collections=collection.related_collections, )
            for collection, tokenized_name in roundrobin(*collections_with_tuples)
            if tokenized_name != tokens
        )

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        # NOT USED?
        input_name = ''.join(tokens)
        collections, _ = self.collection_matcher.search_for_generator(
            tokens,
            input_name,
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
        # if ' ' in name.strip_eth_namehash_unicode_long_name:
        #     return {'tokens': name.strip_eth_namehash_unicode_long_name.strip().split(' ')}
        # else:
        #     return {'tokens': interpretation.tokenization}
        # hack for running ES for only one interpretation/tokenization, e.g. dog -> ['dog'], ['do','g']
        return {'tokens': name.strip_eth_namehash_unicode_long_name.strip().split(' ')}
