from typing import Optional, Any
from generator.generated_name import GeneratedName
from .run_if import RunIf


class RunNever(RunIf):
    
    def should_run(self, names: list[GeneratedName], params: Optional[dict[str, Any]]) -> bool:
        return False
