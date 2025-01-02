from typing import List, Tuple, Optional, Any, Iterable
import logging

from omegaconf import DictConfig

from name_graph.generated_name import GeneratedName
from name_graph.input_name import Interpretation, InputName


logger = logging.getLogger('name_graph')


class NameGenerator:
    """
    Base class for generating names. The class is responsible for generating new
    names based on the already tokenized input. It provides the apply method,
    responsible for registering the applied generators.
    """

    def __init__(self, config: DictConfig):
        self.config = config
        self.limit = config.generation.generator_limits.get(self.__class__.__name__, config.generation.limit)
        self.can_work_with_empty_input = self.__class__.__name__ in config.generation.empty_input_ability
        self._grouping_category = 'unknown'
        self._init_grouping_category()

    def apply(self, name: InputName, interpretation: Interpretation) -> Iterable[GeneratedName]:
        return (
            GeneratedName(generated, grouping_category=self.get_grouping_category(output_name=''.join(generated)),
                          applied_strategies=[[self.__class__.__name__]])
            for generated in self.generate2(name, interpretation)
        )

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        raise NotImplementedError

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        raise NotImplementedError

    def hash(self, name: InputName, interpretation: Interpretation):
        return str(self.prepare_arguments(name, interpretation))

    def _init_grouping_category(self):
        for category_type, gen_list in dictconfig_to_dict(self.config.generation.grouping_categories).items():
            if self.__class__.__name__ in list(gen_list):
                self._grouping_category = category_type
                return
        logger.warning(f'No grouping_category for {self.__class__.__name__} in config; using "unknown" category.')

    def get_grouping_category(self, output_name: Optional[str] = None):
        if self._grouping_category == 'dynamic_':
            raise ValueError(f'"dynamic_" grouping category should be handled by overriding get_grouping_category')
        return self._grouping_category

def dictconfig_to_dict(config: DictConfig):  # todo: move it to utils
    if isinstance(config, DictConfig):
        weights = {}
        for key, value in config.items():
            weights[key] = dictconfig_to_dict(value)
        return weights
    else:
        return config
