from .data import UNICODE_DATA


def name(chr: str, default=None) -> str:
    if len(chr) != 1:
        raise TypeError('name() argument 1 must be a unicode character, not str')
    try:
        return UNICODE_DATA.name(ord(chr))
    except KeyError:
        if default is None:
            raise ValueError('no such name')
        return default


def category(chr: str) -> str:
    if len(chr) != 1:
        raise TypeError('category() argument must be a unicode character, not str')
    try:
        return UNICODE_DATA.category(ord(chr))
    except KeyError:
        return 'Cn'


def combining(chr: str) -> int:
    if len(chr) != 1:
        raise TypeError('combining() argument must be a unicode character, not str')
    try:
        return UNICODE_DATA.combining(ord(chr))
    except KeyError:
        return 0


def block_of(chr: str) -> str:
    if len(chr) != 1:
        raise TypeError('block_of() argument must be a unicode character, not str')
    pass


def script_of(chr: str) -> str:
    pass
