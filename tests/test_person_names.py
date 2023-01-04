import pytest
from pytest import mark
from hydra import initialize, compose

from generator.utils.person_names import PersonNames


@pytest.fixture(scope="module")
def person_names():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        pn = PersonNames(config)
        return pn


def test_person_names(person_names):
    pn = person_names
    assert not pn.tokenize1('information')

    result1 = pn.tokenize1('krzysztofwrobel')
    assert result1[0][1] == 'PL'
    assert result1[0][2] == ('krzysztof', 'wrobel')

    result2 = pn.tokenize1('kwrobel')
    assert result2[0][1] == 'PL'
    assert result2[0][2] == ('k', 'wrobel')

    result3 = pn.tokenize1('wrobel')
    assert result3[0][1] == 'PL'
    assert result3[0][2] == ('wrobel',)

    assert result3[0][0] > result2[0][0] > result1[0][0]


@mark.xfail
@mark.parametrize("name", ['john', 'james', 'david'])
def test_person_names_english_chinese(person_names, name):
    pn = person_names

    result = pn.tokenize1(name)
    assert result[0][1] != 'CN'


def test_person_names_benchmark(person_names, benchmark):
    pn = person_names
    assert not pn.tokenize1('information')

    benchmark(pn.tokenize1, 'the')
