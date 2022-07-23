from .data import UNICODE_DATA


def name(chr: str, default=None) -> str:
    if len(chr) != 1:
        raise TypeError('name() argument 1 must be a unicode character, not str')
    if default is None:
        try:
            return UNICODE_DATA.name[ord(chr)]
        except KeyError:
            raise ValueError('no such name')
    else:
        return UNICODE_DATA.name.get(ord(chr), default)


def category(chr: str) -> str:
    if len(chr) != 1:
        raise TypeError('category() argument must be a unicode character, not str')
    return UNICODE_DATA.category.get(ord(chr), 'Cn')


def combining(chr: str) -> int:
    if len(chr) != 1:
        raise TypeError('combining() argument must be a unicode character, not str')
    return UNICODE_DATA.combining.get(ord(chr), 0)


def block_of(chr: str) -> str:
    if len(chr) != 1:
        raise TypeError('block_of() argument must be a unicode character, not str')
    pass


def script_of(chr: str) -> str:
    pass
