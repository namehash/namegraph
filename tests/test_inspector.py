import pytest
import regex

from hydra import compose, initialize

from inspector.confusables import Confusables
from inspector.features import Features
from inspector.name_inspector import Inspector, remove_accents, strip_accents


def test_inspector():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        inspector = Inspector(config)
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
            print(char, expected_is_confusable, expected_confusables, is_confusable, confusables)
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


def test_inspector_word_length():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('laptop')
        assert result['word_length'] == 1

        result = inspector.analyse_name('lapŁtop')
        assert result['word_length'] == 0

        result = inspector.analyse_name('toplap')
        assert result['word_length'] == 2


def test_inspector_combine():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('laptop😀ą')
        print(result)
        assert 'emoji' in result['any_classes']
        tokenizations = result['tokenizations']
        assert ['laptop', ''] == [token['token'] for token in tokenizations[0]['tokens']]
        assert ['lap', 'top', ''] == [token['token'] for token in tokenizations[1]['tokens']]


@pytest.mark.xfail
def test_inspector_prob():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('😀lap😀')
        # print(result)
        tokenizations = result['tokenizations']
        print(tokenizations)
        assert ['', 'lap', ''] == [token['token'] for token in tokenizations[0]['tokens']]
        assert ['', 'a', ''] == [token['token'] for token in tokenizations[1]['tokens']]


@pytest.mark.timeout(10)
def test_inspector_long():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan')


@pytest.mark.timeout(10)
def test_inspector_long2():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('a' * 40000)


@pytest.mark.timeout(10)
def test_inspector_ner():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('billycorgan', entities=True)
        assert any([t['entities'] for t in result['tokenizations']])


@pytest.mark.timeout(10)
def test_inspector_unknown_name():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91]')
        # TODO


@pytest.mark.timeout(10)
def test_inspector_score():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        inspector = Inspector(config)
        result = inspector.analyse_name('laptop', score=True)
        assert 'score' in result
