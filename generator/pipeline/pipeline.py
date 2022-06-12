import logging
from typing import Set, Tuple

from omegaconf import DictConfig

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

    def apply(self, word: str):
        # the normalizers are applied sequentially
        for normalizer in self.normalizers:
            word = normalizer.normalize(word)

        # the tokenizers are applied in parallel
        decomposition_set: Set[Tuple[str]] = set()
        for tokenizer in self.tokenizers:
            decomposition_set.update(tokenizer.tokenize(word))

        logger.debug(f'Tokenization: {decomposition_set}')

        # the generators are applied sequentially
        suggestions = dict.fromkeys(decomposition_set)
        for generator in self.generators:
            generator_suggestions = {}
            for decomposition in suggestions:
                generator_suggestions.update(dict.fromkeys(generator.generate(decomposition)))

            suggestions = generator_suggestions

        suggestions = [''.join(tokens) for tokens in suggestions]
        logger.info(f'Generated suggestions: {len(suggestions)}')

        # the filters are applied sequentially
        for filter in self.filters:
            logger.debug(f'{filter} filtering')
            suggestions = filter.apply(suggestions)
            logger.debug(f'{filter} done')

        return suggestions

    def _build(self):
        for normalizer_class in self.definition.normalizers:
            self.normalizers.append(globals()[normalizer_class](self.config))

        for tokenizer_class in self.definition.tokenizers:
            self.tokenizers.append(globals()[tokenizer_class](self.config))

        for generator_class in self.definition.generators:
            self.generators.append(globals()[generator_class](self.config))

        for filter_class in self.definition.filters:
            self.filters.append(globals()[filter_class](self.config))
