import pytest

import myunicode


def test_name():
    assert myunicode.name('ア') == 'KATAKANA LETTER A'


def test_name_default():
    assert myunicode.name('🩶', default='default') == 'default'


def test_name_throws_on_missing():
    with pytest.raises(ValueError):
        myunicode.name('🩶')


def test_category():
    assert myunicode.category('ア') == 'Lo'


def test_combining():
    assert myunicode.combining('\u3099') == 8


def test_block_of():
    assert myunicode.block_of('ア') == 'KATAKANA'


def test_script_of():
    assert False


def test_emojis():
    assert '🫶' in myunicode.EMOJIS
