from . import ControlFlow
from ..the_name import TheName, Interpretation


class RunNever(ControlFlow):
    
    def should_run(self, name: TheName, interpretation: Interpretation) -> bool:
        return False
