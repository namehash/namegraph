from typing import List, Dict, Any
import logging
import re

from omegaconf import DictConfig

from generator.generated_name import GeneratedName
from generator.controlflow import *
from generator.normalization import *
from generator.the_name import Interpretation, TheName
from generator.tokenization import *
from generator.generation import *
from generator.filtering import *
from generator.sorting import *
from generator.filtering.subname_filter import SubnameFilter
from generator.filtering.valid_name_filter import ValidNameFilter
from generator.filtering.domain_filter import DomainFilter
from generator.filtering.valid_name_length_filter import ValidNameLengthFilter

from generator.normalization.normalizer import Normalizer
from generator.tokenization.tokenizer import Tokenizer
from generator.generation.name_generator import NameGenerator
from generator.filtering.filter import Filter

from generator.utils import aggregate_duplicates

logger = logging.getLogger('generator')


class PipelineResultsIterator:
    def __init__(self, suggestions: list[GeneratedName]):
        self.index = 0
        self.suggestions = suggestions

    def __len__(self):
        return len(self.suggestions)

    def next_suggestion(self):
        suggestion = self.suggestions[self.index]
        self.index += 1
        return suggestion

    def __iter__(self):
        return self

    def __next__(self) -> GeneratedName:
        # print('ResultsIterator', self.index,len(self.suggestions))
        if self.index < len(self.suggestions):
            suggestion = self.suggestions[self.index]
            self.index += 1
            return suggestion
        raise StopIteration


class Pipeline:
    def __init__(self, definition, config: DictConfig):
        self.definition = definition
        self.config: DictConfig = config
        self.controlflow: List[ControlFlow] = []
        self.normalizers: List[Normalizer] = []
        self.tokenizers: List[Tokenizer] = []
        self.generators: List[NameGenerator] = []
        self.filters: List[Filter] = []
        self._build()

        self.cache = {}

    def clear_cache(self):
        self.cache.clear()

    def apply(self, name: TheName, interpretation: Interpretation) -> PipelineResultsIterator:
        hash = self.generator.hash(name, interpretation)
        # print('HASH', interpretation.tokenization, hash, len(self.cache))
        if hash not in self.cache:
            suggestions = self.generator.apply(name, interpretation)

            for s in suggestions:
                s.pipeline_name = self.definition.name

            for filter_ in self.filters:
                suggestions = filter_.apply(suggestions)
            # remove input name from suggestions
            input_word = re.sub(r'\.\w+$', '', name.strip_eth_namehash)  # TODO niewiadomo jaki jest input
            suggestions = [s for s in suggestions if str(s) != input_word]

            suggestions = aggregate_duplicates(suggestions)

            self.cache[hash] = PipelineResultsIterator(suggestions)

        return self.cache[hash]
        # params = params or dict()
        # 
        # input_word = word
        # words: List[GeneratedName] = [GeneratedName((word,), pipeline_name=self.definition.name)]

        # control flow is applied sequentially
        # TODO
        # for controlflow in self.controlflow:
        #     words = controlflow.apply(words, params=params)

        # the normalizers are applied sequentially
        # for normalizer in self.normalizers:
        #     words = normalizer.apply(words, params=params)

        # the tokenizers are applied in parallel
        # suggestions: List[GeneratedName] = []
        # for tokenizer in self.tokenizers:
        #     suggestions.extend(tokenizer.apply(words, params=params))

        # suggestions = aggregate_duplicates(suggestions, by_tokens=True)
        # logger.debug(f'Tokenization: {suggestions}')
        # 
        # logger.info(
        #     f'Start generation')
        # # the generators are applied sequentially
        # for generator in self.generators:
        #     suggestions = generator.apply(suggestions, params=params)
        # 
        # logger.info(
        #     f'Generated suggestions: {len(suggestions)} - {[str(name)[:30] + "..." if len(str(name)) > 30 else str(name) for name in suggestions[:3]]}')
        # 
        # # the filters are applied sequentially
        # for filter_ in self.filters:
        #     logger.debug(f'{filter} filtering')
        #     suggestions = filter_.apply(suggestions, params=params)
        #     logger.debug(f'{filter} done')
        # 
        # # remove input name from suggestions
        # input_word = re.sub(r'\.\w+$', '', input_word)
        # suggestions = [s for s in suggestions if str(s) != input_word]
        # 
        # logger.info(
        #     f'After filters: {len(suggestions)} - {[str(name)[:30] + "..." if len(str(name)) > 30 else str(name) for name in suggestions[:3]]}')
        # 
        # return aggregate_duplicates(suggestions)

    def _build(self):
        # make control flow optional
        for controlflow_class in getattr(self.definition, 'controlflow', []):
            self.controlflow.append(globals()[controlflow_class](self.config))

        self.generator: NameGenerator = globals()[self.definition.generator](self.config)

        for filter_class in self.definition.filters:
            self.filters.append(globals()[filter_class](self.config))
