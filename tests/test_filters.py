# from generator.filtering import DomainFilter, ValidNameFilter
from hydra import compose, initialize

from generator.filtering.domain_filter import DomainFilter
from generator.filtering.subname_filter import SubnameFilter
from generator.filtering.valid_name_filter import ValidNameFilter


def test_domain_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        filter = DomainFilter(config)
        filtered = [n for n in ('00002', '000436') if filter.filter_name(n)]
        assert '00002' not in filtered
        assert '000436' in filtered


def test_subname_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        filter = SubnameFilter(config)
        filtered = [n for n in ('dog', 'theshit') if filter.filter_name(n)]
        assert 'theshit' not in filtered
        assert 'dog' in filtered


def test_valid_name_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        filter = ValidNameFilter(config)
        filtered = [n for n in ('dog', 'dog.cat', 'do', 'dog-cat', '-dog', 'dog-', 'dog--cat',
                                '$dogcat', '_dogcat', 'dog$cat', 'dogcat_') if filter.filter_name(n)]

        assert 'dog.cat' not in filtered
        assert 'do' not in filtered
        assert 'dog' in filtered
        assert 'dog-cat' in filtered
        assert '-dog' not in filtered
        assert 'dog-' not in filtered
        assert 'dog--cat' in filtered
        assert '$dogcat' in filtered
        assert '_dogcat' in filtered
