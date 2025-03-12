import pytest

from namegraph.domains import Domains
from hydra import compose, initialize


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


def test_domains():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        domains = Domains(config)
        assert 'live' in domains.internet
        assert 'fire' in domains.on_sale
        # assert 'panda' in domains.advertised
        assert '00002' in domains.taken


def test_domains_filtering():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        domains = Domains(config)
        # assert 'orange' in domains.advertised
        # assert 'global' in domains.advertised
        # assert 'orange' not in domains.secondary_market
        # assert 'global' not in domains.secondary_market
        # assert 'global' not in domains.internet
        # assert 'global' not in domains.registered
        assert '00002' in domains.taken
        assert '00002' not in domains.internet
        assert '000' in domains.on_sale
        assert '002' not in domains.taken


def test_domains_singleton():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        domains = Domains(config)
        domains2 = Domains(config)
        assert domains == domains2
        Domains.remove_self()
        domains3 = Domains(config)
        assert domains3 != domains
