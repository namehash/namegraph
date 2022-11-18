from typing import List, Tuple, Optional, Any

from omegaconf import DictConfig

from generator.generated_name import GeneratedName


class NameGenerator:
    """
    Base class for generating names. The class is reposnsible for generating new
    names based on the already tokenized input. It provides the apply method,
    responsible for registering the applied generators.
    """

    def __init__(self, config: DictConfig):
        self.config = config
        self.limit = config.generation.generator_limits.get(self.__class__.__name__, config.generation.limit)

    def apply(
            self,
            tokenized_names: List[GeneratedName],
            params: Optional[dict[str, Any]] = None
    ) -> List[GeneratedName]:
        return [
            GeneratedName(
                generated,
                pipeline_name=name.pipeline_name,
                applied_strategies=[sublist + [self.__class__.__name__] for sublist in name.applied_strategies]
            )
            for name in tokenized_names
            for generated in self.generate(name.tokens, params or dict())
        ]

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        raise NotImplementedError
