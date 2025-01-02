from typing import Optional, Any
from name_graph.generated_name import GeneratedName
from name_graph.input_name import InputName, Interpretation


class ControlFlow:

    def __init__(self, config):
        pass

    def should_run(self, name: InputName, interpretation: Interpretation) -> bool:
        raise NotImplementedError
