import sys

import hydra
from omegaconf import DictConfig
import urllib.request


def download_names(config):
    print('Downloading names', file=sys.stderr)
    urllib.request.urlretrieve(config.app.primary_url, config.app.domains)
    urllib.request.urlretrieve(config.app.secondary_url, config.app.secondary_market_names)
    urllib.request.urlretrieve(config.app.advertised_url, config.app.advertised_names)
    urllib.request.urlretrieve(config.app.subnames_url, config.filtering.subnames)
    urllib.request.urlretrieve(config.app.clubs_url, config.app.clubs)
    print('Downloaded names', file=sys.stderr)
    # urllib.request.urlcleanup()


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def init(config: DictConfig):
    download_names(config)


if __name__ == "__main__":
    init()
