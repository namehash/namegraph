import logging
import re
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

from generator.normalization.normalizer import Normalizer
from generator.tokenization.tokenizer import Tokenizer
from generator.generation.name_generator import NameGenerator
from generator.filtering.filter import Filter

from generator.utils import aggregate_duplicates

logger = logging.getLogger('generator')


class Pipeline:
    def __init__(self, definition, config: DictConfig):
        self.definition = definition
        self.config: DictConfig = config
        self.normalizers: List[Normalizer] = []
        self.tokenizers: List[Tokenizer] = []
        self.generators: List[NameGenerator] = []
        self.filters: List[Filter] = []
        self._build()

    def apply(self, word: str) -> List[GeneratedName]:
        input_word = word
        words: List[GeneratedName] = [GeneratedName((word,))]

        # the normalizers are applied sequentially
        for normalizer in self.normalizers:
            words = normalizer.apply(words)

        # the tokenizers are applied in parallel
        suggestions: List[GeneratedName] = []
        for tokenizer in self.tokenizers:
            suggestions.extend(tokenizer.apply(words))

        suggestions = aggregate_duplicates(suggestions, by_tokens=True)
        logger.debug(f'Tokenization: {suggestions}')

        # the generators are applied sequentially
        for generator in self.generators:
            suggestions = generator.apply(suggestions)

        logger.info(f'Generated suggestions: {len(suggestions)}')

        # the filters are applied sequentially
        for filter_ in self.filters:
            logger.debug(f'{filter} filtering')
            suggestions = filter_.apply(suggestions)
            logger.debug(f'{filter} done')

        # remove input name from suggestions
        input_word = re.sub(r'\.\w+$', '', input_word)
        suggestions = [s for s in suggestions if str(s) != input_word]

        return aggregate_duplicates(suggestions)

    def _build(self):
        for normalizer_class in self.definition.normalizers:
            self.normalizers.append(globals()[normalizer_class](self.config))

        for tokenizer_class in self.definition.tokenizers:
            self.tokenizers.append(globals()[tokenizer_class](self.config))

        for generator_class in self.definition.generators:
            self.generators.append(globals()[generator_class](self.config))

        for filter_class in self.definition.filters:
            self.filters.append(globals()[filter_class](self.config))
