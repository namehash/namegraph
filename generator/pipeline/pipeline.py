import logging
from typing import List, Dict

from omegaconf import DictConfig

from generator.generated_name import GeneratedName
from generator.normalization import *
from generator.tokenization import *
from generator.generation import *
from generator.filtering import *
from generator.sorting import *
from generator.filtering.subname_filter import SubnameFilter
from generator.filtering.valid_name_filter import ValidNameFilter
from generator.filtering.domain_filter import DomainFilter

logger = logging.getLogger('generator')


class Pipeline:
    def __init__(self, definition, config: DictConfig):
        self.definition = definition
        self.config = config
        self.normalizers = []
        self.tokenizers = []
        self.generators = []
        self.filters = []
        self._build()

    def apply(self, word: str) -> List[GeneratedName]:
        input_word = word
        words = [GeneratedName((word,))]

        # the normalizers are applied sequentially
        for normalizer in self.normalizers:
            words = normalizer.apply(words)

        # the tokenizers are applied in parallel
        decomposition_set: Dict[GeneratedName, None] = {}
        for tokenizer in self.tokenizers:
            decomposition_set.update(dict.fromkeys(tokenizer.apply(words)))

        logger.debug(f'Tokenization: {decomposition_set}')

        # the generators are applied sequentially
        suggestions: Dict[GeneratedName, None] = decomposition_set
        for generator in self.generators:
            suggestions = dict.fromkeys(generator.apply(suggestions.keys()))

        # suggestions = [''.join(tokens) for tokens in suggestions]
        logger.info(f'Generated suggestions: {len(suggestions)}')

        # the filters are applied sequentially
        for filter in self.filters:
            logger.debug(f'{filter} filtering')
            suggestions = filter.apply(suggestions)
            logger.debug(f'{filter} done')

        # remove input name from suggestions, duplicates and aggregating metadata
        suggestion2obj: Dict[str, GeneratedName] = dict()
        for suggestion in suggestions:
            word = str(suggestion)

            if word == input_word:
                continue

            duplicate = suggestion2obj.get(word, None)
            if duplicate is not None:
                duplicate.applied_strategies += suggestion.applied_strategies
            else:
                suggestion2obj[word] = suggestion

        return list(suggestion2obj.values())

    def _build(self):
        for normalizer_class in self.definition.normalizers:
            self.normalizers.append(globals()[normalizer_class](self.config))

        for tokenizer_class in self.definition.tokenizers:
            self.tokenizers.append(globals()[tokenizer_class](self.config))

        for generator_class in self.definition.generators:
            self.generators.append(globals()[generator_class](self.config))

        for filter_class in self.definition.filters:
            self.filters.append(globals()[filter_class](self.config))
