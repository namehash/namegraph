from typing import Optional, Any
from namegraph.generated_name import GeneratedName
from namegraph.input_name import InputName, Interpretation


class ControlFlow:

    def __init__(self, config):
        pass

    def should_run(self, name: InputName, interpretation: Interpretation) -> bool:
        raise NotImplementedError
