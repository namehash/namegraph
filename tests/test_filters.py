from hydra import initialize, compose

from generator.filtering import DomainFilter, ValidNameFilter


def test_domain_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = DomainFilter(config)
        filtered = filter.apply(['00002', '00003'])
        assert '00002' not in filtered
        assert '00003' in filtered


def test_valid_name_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = ValidNameFilter(config)
        filtered = filter.apply(['dog', 'dog.cat'])
        assert 'dog.cat' not in filtered
        assert 'dog' in filtered
