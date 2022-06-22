import hydra
from omegaconf import DictConfig


def download_names(config):
    import urllib.request
    urllib.request.urlretrieve(config.app.primary_url, config.app.domains)
    urllib.request.urlretrieve(config.app.secondary_url, config.app.secondary_market_names)
    urllib.request.urlretrieve(config.app.advertised_url, config.app.advertised_names)
    urllib.request.urlretrieve(config.app.subnames_url, config.filtering.subnames)
    # urllib.request.urlcleanup()


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def init(config: DictConfig):
    download_names(config)


if __name__ == "__main__":
    init()
