from typing import Optional, Any
from generator.generated_name import GeneratedName


class ControlFlow:

    def __init__(self, config):
        pass

    def apply(
        self,
        names: list[GeneratedName],
        params: Optional[dict[str, Any]] = None
    ) -> list[GeneratedName]:
        raise NotImplementedError
