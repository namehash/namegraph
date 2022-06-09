from generator.domains import Domains
from hydra import compose, initialize


def test_domain_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        domains = Domains(config)
        assert 'live' in domains.internet
        assert 'fire' in domains.secondary_market
        assert 'panda' in domains.advertised
        assert '00002' in domains.registered
