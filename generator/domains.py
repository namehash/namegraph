import json
import random
from pathlib import Path
from typing import Set, Dict, List, Tuple

# from generator.filtering import SubnameFilter, ValidNameFilter
from generator.filtering.subname_filter import SubnameFilter
from generator.filtering.valid_name_filter import ValidNameFilter
from generator.generated_name import GeneratedName
from generator.normalization.strip_eth_normalizer import strip_eth


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def remove_self(cls):
        if cls in cls._instances:
            del cls._instances[cls]


class Domains(metaclass=Singleton):
    def __init__(self, config):
        self.config = config
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

        self.internet = set(self.validname_filter.filter(self.subname_filter.filter(self.internet)))

    def read_txt(self, path: str) -> Set[str]:
        domains: Set[str] = set()
        with open(path) as domains_file:
            for line in domains_file:
                domain = strip_eth(line.strip())
                domains.add(domain)
        return domains

    def read_json(self, path: str) -> Dict[str, float]:
        names_prices: Dict[str, float] = json.load(open(path))
        names_prices = {strip_eth(name): price for name, price in names_prices.items()}
        # names = self.subname_filter.apply(names_prices.keys())

        # result = {name: names_prices[name] for name in names}

        return names_prices

    def split(self, suggestions: List[GeneratedName], to_match: Dict[str, float]) -> Tuple[
        List[GeneratedName], Dict[GeneratedName, float]]:
        matched: Dict[GeneratedName, float] = {}
        remaining_suggestions: List[GeneratedName] = []
        for suggestion in suggestions:
            suggestion_str = str(suggestion)
            if suggestion_str in to_match:
                matched[suggestion] = to_match[suggestion_str]
            else:
                remaining_suggestions.append(suggestion)
        return remaining_suggestions, matched

    def get_advertised(self, suggestions: List[GeneratedName]) -> Tuple[List[GeneratedName], List[GeneratedName]]:
        remaining_suggestions, advertised = self.split(suggestions, self.advertised)
        return [name_price[0] for name_price in
                sorted(advertised.items(), key=lambda name_price: name_price[1], reverse=True)], remaining_suggestions

    def get_secondary(self, suggestions: List[GeneratedName]) -> Tuple[List[GeneratedName], List[GeneratedName]]:
        remaining_suggestions, secondary = self.split(suggestions, self.secondary_market)
        return [name_price[0] for name_price in secondary.items()], remaining_suggestions

    def get_primary(self, remaining_suggestions: List[GeneratedName]) -> List[GeneratedName]:
        return [s for s in remaining_suggestions if s not in self.registered]
