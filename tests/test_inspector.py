import pytest
import regex

from hydra import compose, initialize

from inspector.confusables import Confusables
from inspector.features import Features
from inspector.name_inspector import Inspector, remove_accents, strip_accents


@pytest.fixture(scope="module")
def prod_inspector():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        inspector = Inspector(config)
        return inspector


@pytest.fixture(scope="module")
def inspector_test_config():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        inspector = Inspector(config)
        return inspector


def test_inspector(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_name('asd')
    print(result)


def test_inspector_character_name():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        f = Features(config)
        assert f.unicodedata_name('a') == 'LATIN SMALL LETTER A'
        assert f.unicodedata_name('🟢') == 'LARGE GREEN CIRCLE'
        assert f.script_name('🩷') == None
        assert f.unicodeblock('🧽') == None


def test_remove_accents():
    chars = {'ą': 'a', 'ś': 's', 'ó': 'o', 'ź': 'z', 'ώ': 'ω', 'ῴ': 'ω'}
    # {'ł':'l','ό':'o'} dont work
    for char, canonical in chars.items():
        assert remove_accents(char) == canonical
        assert strip_accents(char) == canonical


def test_confusable():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        test_confusables = Confusables(config)
        chars = [
            ('ą', True, 'a'),
            ('ś', True, 's'),
            ('ó', True, 'o'),
            ('ź', True, 'z'),
            ('ł', True, 'l'),
            ('ώ', True, 'ω'),
            ('ῴ', True, 'ω'),
            ('𝕤', True, 's'),
            ('ą', True, 'ą'),
            ('s', False, None),
            ('1', False, None),
            ('l', False, None),
            ('⒀', True, '(13)'),
        ]
        for char, expected_is_confusable, expected_confusables in chars:
            is_confusable, confusables = test_confusables.analyze(char)
            # print(char, expected_is_confusable, expected_confusables, is_confusable, confusables)
            assert is_confusable == expected_is_confusable
            if is_confusable:
                assert expected_confusables in confusables


def test_confusable_simple():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        confusables = Confusables(config)

        for k, v in confusables.confusable_chars.items():
            if regex.match(r'[a-z0-9-]', k, regex.ASCII):
                print([k, v], len(k), len(v))


def test_inspector_word_count(inspector_test_config):
    inspector = inspector_test_config
    result = inspector.analyse_name('laptop')
    assert result['word_count'] == 1

    result = inspector.analyse_name('lapŁtop')
    assert result['word_count'] == 0

    result = inspector.analyse_name('toplap')
    assert result['word_count'] == 2


def test_inspector_combine(inspector_test_config):
    inspector = inspector_test_config
    result = inspector.analyse_name('laptop😀ą')
    print(result)
    assert 'emoji' in result['any_classes']
    tokenizations = result['tokenizations']
    assert ['laptop', ''] == [token['token'] for token in tokenizations[0]['tokens']]
    assert ['lap', 'top', ''] == [token['token'] for token in tokenizations[1]['tokens']]


@pytest.mark.xfail
def test_inspector_prob(inspector_test_config):
    inspector = inspector_test_config
    result = inspector.analyse_name('😀lap😀')
    # print(result)
    tokenizations = result['tokenizations']
    print(tokenizations)
    assert ['', 'lap', ''] == [token['token'] for token in tokenizations[0]['tokens']]
    assert ['', 'a', ''] == [token['token'] for token in tokenizations[1]['tokens']]


@pytest.mark.execution_timeout(10)
def test_inspector_long(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_name('miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan')


@pytest.mark.execution_timeout(10)
def test_inspector_long2(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_name('a' * 40000)


@pytest.mark.execution_timeout(10)
def test_inspector_ner(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_name('billycorgan', entities=True)
    assert any([t['entities'] for t in result['tokenizations']])


@pytest.mark.execution_timeout(10)
def test_inspector_unknown_name(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_name('[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91]')
    # TODO


@pytest.mark.execution_timeout(10)
def test_inspector_score(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_name('laptop', tokenization=True)
    assert 'score' in result


@pytest.mark.execution_timeout(10)
def test_inspector_score_long(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_name('laptoplaptoplaptoplaptoplaptop', tokenization=True)
    assert 'score' in result


@pytest.mark.execution_timeout(10)
def test_inspector_limit_confusables(prod_inspector):
    inspector = prod_inspector

    result = inspector.analyse_name('ąlaptop', limit_confusables=True)
    assert len(result['chars'][0]['confusables']) == 1

    result = inspector.analyse_name('ąlaptop', limit_confusables=False)
    assert len(result['chars'][0]['confusables']) > 1


@pytest.mark.execution_timeout(10)
def test_inspector_disable_chars_output(prod_inspector):
    inspector = prod_inspector

    result = inspector.analyse_name('ąlaptop', disable_chars_output=True)
    assert result['chars'] is None
    assert len(result['any_classes']) >= 1

    result = inspector.analyse_name('ąlaptop', disable_chars_output=False)
    assert len(result['chars']) == 7


@pytest.mark.execution_timeout(10)
def test_inspector_disable_char_analysis(prod_inspector):
    inspector = prod_inspector

    result = inspector.analyse_name('ąlaptop', disable_char_analysis=True)
    assert result['chars'] is None
    assert 'any_classes' not in result
    print(result)

    result = inspector.analyse_name('ąlaptop', disable_char_analysis=False)
    assert len(result['chars']) == 7


def test_inspector_numerics():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        features = Features(config)
        
        with open('tests/data/unicode_numerics.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or line.startswith('#'):
                    continue

                char = chr(int(line, 16))
                assert features.is_number(char), f'{line} not detected as number'
