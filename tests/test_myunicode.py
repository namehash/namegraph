import pytest

import myunicode


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'LATIN SMALL LETTER A'),
        ('ア', 'KATAKANA LETTER A'),
        ('ἀ', 'GREEK SMALL LETTER ALPHA WITH PSILI'),
        ('יִ', 'HEBREW LETTER YOD WITH HIRIQ'),
        ('\u3099', 'COMBINING KATAKANA-HIRAGANA VOICED SOUND MARK'),
    ]
)
def test_name(chr, expected):
    assert myunicode.name(chr) == expected
    assert myunicode.name(chr, 'default') == expected


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'LATIN SMALL LETTER A'),
        ('🩶', 'default'),
    ]
)
def test_name_default(chr, expected):
    assert myunicode.name(chr, default='default') == expected


@pytest.mark.parametrize('chr', ['🩶'])
def test_name_throws_on_missing(chr):
    with pytest.raises(ValueError, match='no such name'):
        myunicode.name(chr)


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_name_throws_on_str(chr):
    with pytest.raises(TypeError, match=r'name\(\) argument 1 must be a unicode character, not str'):
        myunicode.name(chr)
    with pytest.raises(TypeError, match=r'name\(\) argument 1 must be a unicode character, not str'):
        myunicode.name(chr, 'default')


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'Ll'),
        ('ア', 'Lo'),
        ('\u0600', 'Cf'),
        ('🩶', 'Cn'),
    ]
)
def test_category(chr, expected):
    assert myunicode.category(chr) == expected


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_category_throws_on_str(chr):
    with pytest.raises(TypeError, match=r'category\(\) argument must be a unicode character, not str'):
        myunicode.category(chr)


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 0),
        ('🩶', 0),
        ('\u3099', 8),
    ]
)
def test_combining(chr, expected):
    assert myunicode.combining(chr) == expected


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_combining_throws_on_str(chr):
    with pytest.raises(TypeError, match=r'combining\(\) argument must be a unicode character, not str'):
        myunicode.combining(chr)


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'Basic Latin'),
        ('ア', 'Katakana'),
        ('🩶', 'Symbols and Pictographs Extended-A'),
    ]
)
def test_block_of(chr, expected):
    assert myunicode.block_of(chr) == expected


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_block_of_throws_on_str(chr):
    with pytest.raises(Exception, match=r'block_of\(\) argument must be a unicode character, not str'):
        myunicode.block_of(chr)


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('יִ', 'Hebrew'),
        ('a', 'Latin'),
        ('abc', 'Latin'),
        ('ア', 'Katakana'),
        ('アア', 'Katakana'),
        ('aア', None),
        ('Mały kotek', 'Latin'),
        ('その目、誰の目？', None),
        ('そのめ、だれのめ？', 'Hiragana'),
        ('そのめ,だれのめ...?', 'Hiragana'),
        ('لوحة المفاتيح العربية', 'Arabic'),
        ('Those eyes, だれのめ?', None),
    ]
)
def test_script_of(chr, expected):
    assert myunicode.script_of(chr) == expected


def test_script_throws_on_empty():
    with pytest.raises(TypeError):
        myunicode.script_of('')


@pytest.mark.parametrize('emoji', ['🫶'])
def test_emojis(emoji):
    assert emoji in myunicode.EMOJIS
