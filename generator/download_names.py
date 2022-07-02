import sys

import hydra
from omegaconf import DictConfig
import urllib.request

from pathlib import Path


def download_file(url, path, override=True):
    print('Downloading?', url, path, file=sys.stderr)
    if not Path(path).exists() or override:
        print('Downloading', url, path, file=sys.stderr)
        urllib.request.urlretrieve(url, path)


def download_names(config):
    print('Downloading names', file=sys.stderr)
    download_file(config.app.primary_url, config.app.domains)
    download_file(config.app.secondary_url, config.app.secondary_market_names)
    download_file(config.app.advertised_url, config.app.advertised_names)
    download_file(config.app.subnames_url, config.filtering.subnames)
    download_file(config.app.clubs_url, config.app.clubs)
    print('Downloaded names', file=sys.stderr)
    # urllib.request.urlcleanup()


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def init(config: DictConfig):
    download_names(config)


if __name__ == "__main__":
    init()
