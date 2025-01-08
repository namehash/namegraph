import pytest
from pytest import mark
from hydra import initialize, compose

from namegraph.utils.person_names import PersonNames
from namegraph.input_name import InputName
from namegraph.classifier.person_name_classifier import PersonNameClassifier


@pytest.fixture(scope="module")
def person_names():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pn = PersonNames(config)
        return pn


def test_person_names(person_names):
    pn = person_names
    assert not pn.tokenize('information')

    result1 = pn.tokenize('krzysztofwrobel')
    assert result1[0][1] == 'PL'
    assert result1[0][2] == ('krzysztof', 'wrobel')

    result2 = pn.tokenize('kwrobel')
    assert result2[0][1] == 'PL'
    assert result2[0][2] == ('k', 'wrobel')

    result3 = pn.tokenize('wrobel')
    assert result3[0][1] == 'PL'
    assert result3[0][2] == ('wrobel',)

    assert result3[0][0] > result2[0][0] > result1[0][0]


@mark.xfail
@mark.parametrize("name", ['john', 'james', 'david'])
def test_person_names_english_chinese(person_names, name):
    pn = person_names

    result = pn.tokenize(name)
    assert result[0][1] != 'CN'


def test_person_names_benchmark(person_names, benchmark):
    pn = person_names
    assert not pn.tokenize('information')

    benchmark(pn.tokenize, 'the')


def test_person_name_classifier_returns_language():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pn_cls = PersonNameClassifier(config)

        def classify_and_assert_lang(lang: str):
            nonlocal name, pn_cls
            name.strip_eth_namehash_unicode_replace_invalid = name.input_name
            pn_cls.classify(name)
            assert all([interpretations[0].lang == lang for interpretations in name.interpretations.values()])

        name = InputName('kendrick', {})
        classify_and_assert_lang('en')

        name = InputName('małgorzata', {})
        classify_and_assert_lang('pl')

        name = InputName('noemie', {})
        classify_and_assert_lang('fr')

        name = InputName('alejandra', {})
        classify_and_assert_lang('es')

        name = InputName('boglarka', {})
        classify_and_assert_lang('hu')
