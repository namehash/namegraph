from typing import List, Tuple, Optional, Any

from omegaconf import DictConfig

from generator.generated_name import GeneratedName
from generator.input_name import Interpretation, InputName


class NameGenerator:
    """
    Base class for generating names. The class is reposnsible for generating new
    names based on the already tokenized input. It provides the apply method,
    responsible for registering the applied generators.
    """

    def __init__(self, config: DictConfig):
        self.config = config
        self.limit = config.generation.generator_limits.get(self.__class__.__name__, config.generation.limit)
        self.can_work_with_empty_input = self.__class__.__name__ in config.generation.empty_input_ability

    def apply(self, name: InputName, interpretation: Interpretation) -> list[GeneratedName]:
        return [
            GeneratedName(generated, applied_strategies=[[self.__class__.__name__]])
            for generated in self.generate2(name, interpretation)
        ]

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        raise NotImplementedError

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        raise NotImplementedError

    def hash(self, name: InputName, interpretation: Interpretation):
        return str(self.prepare_arguments(name, interpretation))
