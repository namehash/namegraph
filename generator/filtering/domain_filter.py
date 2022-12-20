from generator.domains import Domains
from .filter import Filter


class DomainFilter(Filter):
    """Filter registered domains."""

    def __init__(self, config):
        super().__init__()
        self.domains = Domains(config)

    def filter_name(self, name: str) -> bool:
        return name not in self.domains.taken
