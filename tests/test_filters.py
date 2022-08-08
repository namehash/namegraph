# from generator.filtering import DomainFilter, ValidNameFilter
from hydra import compose, initialize_config_module, initialize

import pytest
from pytest import mark
from typing import List

from generator.filtering.domain_filter import DomainFilter
from generator.filtering.subname_filter import SubnameFilter
from generator.filtering.valid_name_filter import ValidNameFilter


def test_domain_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = DomainFilter(config)
        filtered = filter.filter(['00002', '000436'])
        assert '00002' not in filtered
        assert '000436' in filtered


def test_subname_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = SubnameFilter(config)
        result = filter.filter(['dog', 'theshit'])
        assert 'theshit' not in result
        assert 'dog' in result


def test_valid_name_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = ValidNameFilter(config)
        filtered = filter.filter(['dog', 'dog.cat', 'do', 'dog-cat', '-dog', 'dog-', 'dog--cat'])
        assert 'dog.cat' not in filtered
        assert 'do' not in filtered
        assert 'dog' in filtered
        assert 'dog-cat' in filtered
        assert '-dog' not in filtered
        assert 'dog-' not in filtered
        assert 'dog--cat' in filtered
