from . import ControlFlow
from ..input_name import InputName, Interpretation


class RunNever(ControlFlow):
    
    def should_run(self, name: InputName, interpretation: Interpretation) -> bool:
        return False
