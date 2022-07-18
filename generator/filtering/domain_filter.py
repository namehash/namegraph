from typing import Iterable, List

from generator.domains import Domains


class DomainFilter:
    """Filter registered domains."""

    def __init__(self, config):
        self.domains = Domains(config)

    def apply(self, names: Iterable[str]) -> List[str]:
        return [n for n in names if n not in self.domains.registered]
