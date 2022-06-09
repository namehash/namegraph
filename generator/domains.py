import json
from pathlib import Path
from typing import Set, Dict


class Domains:
    def __init__(self, config):
        # self.config = config
        self.registered: Set[str] = self.read_txt(Path(config.filtering.root_path) / config.filtering.domains)
        self.secondary_market: Dict[str, int] = self.read_json(config.app.secondary_market_names)
        self.advertised: Dict[str, int] = self.read_json(config.app.advertised_names)
        self.internet: Set[str] = self.read_txt(config.app.internet_domains)

    def read_txt(self, path):
        domains: Set[str] = set()
        with open(path) as domains_file:
            for line in domains_file:
                domain = line.strip()
                if domain.endswith('.eth'):
                    domain = domain[:-4]
                domains.add(domain)
        return domains

    def read_json(self, path):
        names = json.load(open(path))
        names = {k[:-4] if k.endswith('.eth') else k: v for k, v in names.items()}
        return names