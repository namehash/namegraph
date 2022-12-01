import pytest
from generator.utils.unicode_wrap import unicode_wrap, unicode_unwrap


def test_wrap():
    assert unicode_wrap('foo bar') == '|66|6f|6f|20|62|61|72|'


def test_unwrap():
    assert unicode_unwrap('|66|6f|6f|20|62|61|72|') == 'foo bar'


def test_empty():
    assert unicode_wrap('') == ''
    assert unicode_unwrap('') == ''


@pytest.mark.parametrize('text', [
    '|', '||', '|||', '|66||',
])
def test_invalid(text):
    with pytest.raises(Exception):
        unicode_unwrap(text)
