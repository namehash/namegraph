from typing import Optional, Any
from generator.generated_name import GeneratedName
from .run_if import RunIf


class RunIfNotConservative(RunIf):
    
    def should_run(self, names: list[GeneratedName], params: Optional[dict[str, Any]]) -> bool:
        return not params.get('conservative', False)
