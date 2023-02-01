from . import ControlFlow
from ..the_name import TheName, Interpretation


class RunIfNotConservative(ControlFlow):

    def should_run(self, name: TheName, interpretation: Interpretation) -> bool:
        return not name.params.get('conservative', False)
