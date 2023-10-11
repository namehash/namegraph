from __future__ import annotations

import time
from typing import List
import logging
import re

from omegaconf import DictConfig
from omegaconf.errors import ConfigAttributeError

from generator.pipeline.pipeline_results_iterator import PipelineResultsIterator
from generator.input_name import Interpretation, InputName

from generator.controlflow import *
from generator.generation import *
from generator.filtering import *

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


def dictconfig_to_dict(config: DictConfig):
    if isinstance(config, DictConfig):
        weights = {}
        for key, value in config.items():
            weights[key] = dictconfig_to_dict(value)
        return weights
    else:
        return config


class Pipeline:
    def __init__(self, definition, config: DictConfig):
        self.definition = definition
        self.pipeline_name = definition.name
        try:  # copy to internal dict
            self.weights = dictconfig_to_dict(definition.weights)
        except ConfigAttributeError:
            pass
        try:  # copy to internal dict
            self.mode_weights_multiplier = dictconfig_to_dict(definition.mode_weights_multiplier)
        except ConfigAttributeError:
            self.mode_weights_multiplier = {}

        try:  # copy to internal dict
            self.global_limits = dictconfig_to_dict(definition.global_limits)
        except ConfigAttributeError:
            self.global_limits = {}

        try:  # copy to internal dict
            self.category_limits = dictconfig_to_dict(definition.category_limits)
        except ConfigAttributeError:
            self.category_limits = {}

        self.config: DictConfig = config
        self.controlflow: List[ControlFlow] = []
        self.generators: List[NameGenerator] = []
        self.filters: List[Filter] = []

        logger.info(f'Pipeline {self.pipeline_name} initing.')
        self._build()

        self.cache = {}
        logger.info(f'Pipeline {self.pipeline_name} inited.')

    def __eq__(self, other: Pipeline) -> bool:
        return isinstance(other, Pipeline) and self.pipeline_name == other.pipeline_name

    def __hash__(self) -> int:
        return hash(self.pipeline_name)

    def clear_cache(self):
        """Cache must be cleared before every request because index in pipeline results is saved."""
        self.cache.clear()

    def apply(self, name: InputName, interpretation: Interpretation | None) -> PipelineResultsIterator:
        """
        Generate suggestions, results are cached.
        """
        if interpretation:
            logger.debug(
                f'Pipeline {self.pipeline_name} suggestions apply on I {interpretation.type} {str(interpretation.tokenization)}.')
        else:
            logger.debug(f'Pipeline {self.pipeline_name} suggestions apply on N {name.input_name}.')

        hash = self.generator.hash(name, interpretation)
        # print('HASH', interpretation.tokenization, hash, len(self.cache))
        if hash not in self.cache:
            should_run = all([controlflow.should_run(name, interpretation) for controlflow in self.controlflow])
            if should_run:  # TODO ok?

                if interpretation:
                    logger.debug(
                        f'Pipeline {self.pipeline_name} suggestions generation on I {interpretation.type} {str(interpretation.tokenization)}.')
                else:
                    logger.debug(f'Pipeline {self.pipeline_name} suggestions generation on N {name.input_name}.')
                start_time = time.time()
                suggestions = self.generator.apply(name, interpretation)
                generator_time = 1000 * (time.time() - start_time)
                logger.info(f'Pipeline {self.pipeline_name} suggestions generated. Time: {generator_time:.2f}')

                for filter_ in self.filters:
                    suggestions = filter_.apply(suggestions)
                # remove input name from suggestions
                input_word = re.sub(r'\.\w+$', '', name.strip_eth_namehash).replace(' ', '')  # TODO niewiadomo jaki jest input
                suggestions = (s for s in suggestions if str(s) != input_word)

                # suggestions = aggregate_duplicates(suggestions)

                # TODO: add metadata about types and interpretation
                def gen(suggestions):
                    for s in suggestions:
                        s.pipeline_name = self.pipeline_name
                        s.interpretation = (
                            interpretation.type if interpretation else None,
                            interpretation.lang if interpretation else None,
                            hash)  # TODO because of caching interpretation's type and lang might be wrong
                        yield s

                suggestions = gen(suggestions)

            else:
                suggestions = []
            self.cache[hash] = PipelineResultsIterator(suggestions)
            logger.debug(f'Pipeline {self.pipeline_name} suggestions cached.')
        return self.cache[hash]

    def _build(self):
        # make control flow optional
        for controlflow_class in getattr(self.definition, 'controlflow', []):
            self.controlflow.append(globals()[controlflow_class](self.config))

        self.generator: NameGenerator = globals()[self.definition.generator](self.config)

        for filter_class in self.definition.filters:
            self.filters.append(globals()[filter_class](self.config))
