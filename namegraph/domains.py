import csv
import logging
from pathlib import Path
from typing import Set, Dict, Optional

from namegraph.filtering.subname_filter import SubnameFilter
from namegraph.filtering.valid_name_filter import ValidNameFilter
from namegraph.generated_name import GeneratedName
from namegraph.normalization.strip_eth_normalizer import strip_eth
from namegraph.utils import Singleton

logger = logging.getLogger('namegraph')


class Domains(metaclass=Singleton):
    TAKEN = 'taken'
    ON_SALE = 'on_sale'
    AVAILABLE = 'available'
    RECENTLY_RELEASED = 'recently_released'

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
                if status == self.TAKEN or status == self.RECENTLY_RELEASED:
                    taken[name] = interesting_score
                elif status == self.ON_SALE:
                    on_sale[name] = interesting_score
                elif status == self.AVAILABLE:
                    available[name] = interesting_score

        return taken, on_sale, available

    def get_name_status(self, name: str) -> str:
        if name in self.on_sale:
            return self.ON_SALE
        elif name in self.taken:
            return self.TAKEN
        else:
            return self.AVAILABLE

    def get_interesting_score(self, name: GeneratedName) -> Optional[float]:
        if name.status is None:
            name.status = self.get_name_status(str(name))

        if name.status in [self.TAKEN, self.RECENTLY_RELEASED]:
            return self.taken.get(str(name), None)
        if name.status == self.AVAILABLE:
            return self.available.get(str(name), None)
        if name.status == self.ON_SALE:
            return self.on_sale.get(str(name), None)

        return None
