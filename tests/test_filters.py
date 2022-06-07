from generator.filtering import DomainFilter, ValidNameFilter
from hydra import compose, initialize_config_module, initialize

import pytest
from pytest import mark
from typing import List

from generator.filtering import DomainFilter, SubnameFilter


def test_domain_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = DomainFilter(config)
        filtered = filter.apply(['00002', '00003'])
        assert '00002' not in filtered
        assert '00003' in filtered


def test_subname_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = SubnameFilter(config)
        result = filter.apply(['dog', 'theshit'])
        assert 'theshit' not in result
        assert 'dog' in result


def test_valid_name_filter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        filter = ValidNameFilter(config)
        filtered = filter.apply(['dog', 'dog.cat', 'do'])
        assert 'dog.cat' not in filtered
        assert 'do' not in filtered
        assert 'dog' in filtered
