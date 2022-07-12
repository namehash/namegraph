import sys

import hydra
from omegaconf import DictConfig

from download_from_s3 import S3Downloader


def download_names(config):
    print('Downloading names', file=sys.stderr)
    s3_downloader = S3Downloader()
    s3_downloader.download_file(config.app.primary_url, config.app.domains)
    s3_downloader.download_file(config.app.secondary_url, config.app.secondary_market_names)
    s3_downloader.download_file(config.app.advertised_url, config.app.advertised_names)
    s3_downloader.download_file(config.app.subnames_url, config.filtering.subnames)
    s3_downloader.download_file(config.app.clubs_url, config.app.clubs)
    print('Downloaded names', file=sys.stderr)


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def init(config: DictConfig):
    download_names(config)


if __name__ == "__main__":
    init()
