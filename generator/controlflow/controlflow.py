from typing import Optional, Any
from generator.generated_name import GeneratedName
from generator.the_name import TheName, Interpretation


class ControlFlow:

    def __init__(self, config):
        pass

    def should_run(self, name: TheName, interpretation: Interpretation) -> bool:
        raise NotImplementedError
