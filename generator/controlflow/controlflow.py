from typing import Optional, Any
from generator.generated_name import GeneratedName
from generator.input_name import InputName, Interpretation


class ControlFlow:

    def __init__(self, config):
        pass

    def should_run(self, name: InputName, interpretation: Interpretation) -> bool:
        raise NotImplementedError
