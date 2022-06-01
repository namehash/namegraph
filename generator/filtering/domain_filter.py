from pathlib import Path

class DomainFilter:
    def __init__(self, config):
        self.domains = set()
        with open(Path(config.filtering.root_path) / config.filtering.domains) as domains_file:
            for line in domains_file:
                self.domains.add(line.strip()[:-4])


    def apply(self, names):
        return [n for n in names if n not in self.domains]
