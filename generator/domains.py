import csv
import logging
from pathlib import Path
from typing import Set, Dict, List, Tuple

from generator.filtering.subname_filter import SubnameFilter
from generator.filtering.valid_name_filter import ValidNameFilter
from generator.generated_name import GeneratedName
from generator.normalization.strip_eth_normalizer import strip_eth

logger = logging.getLogger('generator')


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
        logger.debug('Initing Domains')
        self.config = config
        self.subname_filter = SubnameFilter(config)
        self.validname_filter = ValidNameFilter(config)

        self.taken, self.on_sale, self.available = self.read_csv_domains(
            Path(config.filtering.root_path) / config.app.domains)
        self.taken: Dict[
            str, float]  # = self.read_csv(Path(config.filtering.root_path) / config.filtering.domains)
        self.on_sale: Dict[str, float]  # = self.read_csv_with_prices(config.app.secondary_market_names)
        # self.advertised: Dict[str, float] = self.read_csv_with_prices(config.app.advertised_names)
        self.internet: Set[str] = self.read_csv(config.app.internet_domains)

        # for k in self.advertised:
        #     self.secondary_market.pop(k, None)
        # self.registered -= self.secondary_market.keys()
        # self.registered -= self.advertised.keys()

        self.internet -= self.taken.keys()
        self.internet -= self.on_sale.keys()
        # self.internet -= self.advertised.keys()

        self.internet = set(
            n for n in self.internet
            if self.validname_filter.filter_name(n) and self.subname_filter.filter_name(n)
        )
        self.only_available = {
            n: v for n, v in self.available.items()
            if self.validname_filter.filter_name(n) and self.subname_filter.filter_name(n)
        }
        logger.debug('Inited Domains')

    def read_csv(self, path: str) -> Set[str]:
        domains: Set[str] = set()
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                assert len(row) == 1
                name = strip_eth(row[0])
                domains.add(name)
        return domains

    # def read_csv_with_prices(self, path: str) -> Dict[str, float]:
    #     names_prices: Dict[str, float] = {}
    #     with open(path, newline='') as csvfile:
    #         reader = csv.reader(csvfile)
    #         next(reader)
    #         for row in reader:
    #             assert len(row) == 2
    #             name = strip_eth(row[0])
    #             names_prices[name] = float(row[1])
    #     return names_prices

    def read_csv_domains(self, path: str) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
        taken: Dict[str, float] = {}
        on_sale: Dict[str, float] = {}
        available: Dict[str, float] = {}
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                assert len(row) == 3
                name, interesting_score, status = row
                name = strip_eth(name)
                interesting_score = float(interesting_score)
                if status == 'taken' or status == 'recently_released':
                    taken[name] = interesting_score
                elif status == 'on_sale':
                    on_sale[name] = interesting_score
                elif status == 'available':
                    available[name] = interesting_score

        return taken, on_sale, available

    def get_name_status(self, name: str):
        if name in self.on_sale:
            return 'on_sale'
        elif name in self.taken:
            return 'taken'
        else:
            return 'available'

    def split(self, suggestions: List[GeneratedName], to_match: Dict[str, float]) \
            -> Tuple[List[GeneratedName], Dict[GeneratedName, float]]:

        matched: Dict[GeneratedName, float] = {}
        remaining_suggestions: List[GeneratedName] = []
        for suggestion in suggestions:
            suggestion_str = str(suggestion)
            if suggestion_str in to_match:
                matched[suggestion] = to_match[suggestion_str]
            else:
                remaining_suggestions.append(suggestion)
        return remaining_suggestions, matched

    def get_on_sale(self, suggestions: List[GeneratedName]) -> Tuple[List[GeneratedName], List[GeneratedName]]:
        remaining_suggestions, on_sale = self.split(suggestions, self.on_sale)
        return [name_price[0] for name_price in on_sale.items()], remaining_suggestions

    def get_available(self, suggestions: List[GeneratedName]) -> Tuple[List[GeneratedName], List[GeneratedName]]:
        available = [s for s in suggestions if str(s) not in self.taken]
        remaining = [s for s in suggestions if str(s) in self.taken]
        return available, remaining
