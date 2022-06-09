import json
from pathlib import Path
from typing import Set, Dict

from generator.filtering import SubnameFilter, ValidNameFilter


class Domains:
    def __init__(self, config):
        self.subname_filter = SubnameFilter(config)
        self.validname_filter = ValidNameFilter(config)

        self.registered: Set[str] = self.read_txt(Path(config.filtering.root_path) / config.filtering.domains)
        self.secondary_market: Dict[str, float] = self.read_json(config.app.secondary_market_names)
        self.advertised: Dict[str, float] = self.read_json(config.app.advertised_names)
        self.internet: Set[str] = self.read_txt(config.app.internet_domains)

        for k in self.advertised:
            self.secondary_market.pop(k, None)
        self.registered -= self.secondary_market.keys()
        self.registered -= self.advertised.keys()

        self.internet -= self.registered
        self.internet -= self.secondary_market.keys()
        self.internet -= self.advertised.keys()

        self.internet = set(self.validname_filter.apply(self.subname_filter.apply(self.internet)))

    def read_txt(self, path) -> Set[str]:
        domains: Set[str] = set()
        with open(path) as domains_file:
            for line in domains_file:
                domain = line.strip()
                if domain.endswith('.eth'):
                    domain = domain[:-4]
                domains.add(domain)
        return domains

    def read_json(self, path) -> Dict[str, float]:
        names_prices: Dict[str, float] = json.load(open(path))
        names_prices = {(name[:-4] if name.endswith('.eth') else name): price for name, price in names_prices.items()}
        names = self.subname_filter.apply(names_prices.keys())

        result = {name: names_prices[name] for name in names}

        return result
