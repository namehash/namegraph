from typing import Optional, Any
from generator.generated_name import GeneratedName
from .controlflow import ControlFlow


class RunIf(ControlFlow):
    
    def apply(
        self,
        names: list[GeneratedName],
        params: Optional[dict[str, Any]] = None
    ) -> list[GeneratedName]:
        return names if self.should_run(names, params) else []

    def should_run(self, names: list[GeneratedName], params: Optional[dict[str, Any]]) -> bool:
        raise NotImplementedError
