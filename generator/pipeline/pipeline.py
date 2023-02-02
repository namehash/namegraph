from typing import List
import logging
import re

from omegaconf import DictConfig

from generator.controlflow import *
from generator.pipeline.pipeline_results_iterator import PipelineResultsIterator
from generator.input_name import Interpretation, InputName

from generator.controlflow import *
from generator.normalization import *
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


class Pipeline:
    def __init__(self, definition, config: DictConfig):
        self.definition = definition
        self.pipeline_name = definition.name
        self.config: DictConfig = config
        self.controlflow: List[ControlFlow] = []
        self.normalizers: List[Normalizer] = []
        self.tokenizers: List[Tokenizer] = []
        self.generators: List[NameGenerator] = []
        self.filters: List[Filter] = []

        logger.info(f'Pipeline {self.definition.name} initing.')
        self._build()

        self.cache = {}
        logger.info(f'Pipeline {self.definition.name} inited.')

    def clear_cache(self):
        self.cache.clear()

    def apply(self, name: InputName, interpretation: Interpretation) -> PipelineResultsIterator:
        if interpretation:
            logger.info(
                f'Pipeline {self.definition.name} suggestions apply on I {interpretation.type} {str(interpretation.tokenization)}.')
        else:
            logger.info(f'Pipeline {self.definition.name} suggestions apply on N {name.input_name}.')

        hash = self.generator.hash(name, interpretation)
        # print('HASH', interpretation.tokenization, hash, len(self.cache))
        if hash not in self.cache:
            should_run = [controlflow.should_run(name, interpretation) for controlflow in self.controlflow]
            if all(should_run):  # TODO ok?

                if interpretation:
                    logger.info(
                        f'Pipeline {self.definition.name} suggestions generation on I {interpretation.type} {str(interpretation.tokenization)}.')
                else:
                    logger.info(f'Pipeline {self.definition.name} suggestions generation on N {name.input_name}.')

                suggestions = self.generator.apply(name, interpretation)
                logger.info('Pipeline suggestions generated.')

                for s in suggestions:
                    s.pipeline_name = self.pipeline_name

                for filter_ in self.filters:
                    suggestions = filter_.apply(suggestions)
                # remove input name from suggestions
                input_word = re.sub(r'\.\w+$', '', name.strip_eth_namehash)  # TODO niewiadomo jaki jest input
                suggestions = [s for s in suggestions if str(s) != input_word]

                suggestions = aggregate_duplicates(suggestions)
            else:
                suggestions = []
            self.cache[hash] = PipelineResultsIterator(suggestions)
            logger.info('Pipeline suggestions cached.')
        return self.cache[hash]

    def _build(self):
        # make control flow optional
        for controlflow_class in getattr(self.definition, 'controlflow', []):
            self.controlflow.append(globals()[controlflow_class](self.config))

        self.generator: NameGenerator = globals()[self.definition.generator](self.config)

        for filter_class in self.definition.filters:
            self.filters.append(globals()[filter_class](self.config))
