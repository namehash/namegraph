import re

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
    # chars.update({'ł':'l','ό':'o'}) #dont work
    for char, canonical in chars.items():
        assert remove_accents(char) == canonical
        assert strip_accents(char) == canonical


def test_confusable():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        test_confusables = Confusables(config)
        chars = {
            'ą': (True, 'a'),
            'ś': (True, 's'),
            'ó': (True, 'o'),
            'ź': (True, 'z'),
            'ł': (True, 'l'),
            'ώ': (True, 'ω'),
            'ῴ': (True, 'ω'),
            # 'ω': (True, 'ω'),
            '𝕤': (True, 's'),
            # 'ą': (True, 'a'),
            's': (False, None),
            '1': (False, None),
            'l': (False, None),
            '⒀': (True, '(13)'),
        }
        # chars.update({'ł':'l','ό':'o'}) #dont work
        for char, expected in chars.items():
            is_confusable, confusables = test_confusables.analyze(char)
            print(char, expected, is_confusable, confusables)
            assert is_confusable == expected[0]
            if is_confusable:
                assert expected[1] in confusables


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
        result = inspector.analyse_name('laptop😀')
        assert 'emoji' in result['any_classes']
