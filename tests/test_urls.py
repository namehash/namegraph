from hydra import initialize, compose
import requests


def check_url(url):
    r = requests.head(url)
    assert r.status_code == 200


def test_urls():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        check_url(config.generation.word2vec_url)
        check_url(config.generation.wikipedia2vec_url)
        check_url(config.app.primary_url)
        check_url(config.app.secondary_url)
        check_url(config.app.advertised_url)
        check_url(config.app.subnames_url)
        check_url(config.app.clubs_url)
