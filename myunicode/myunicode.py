from .data import UNICODE_DATA


def name(chr: str, default=None) -> str:
    if default is None:
        try:
            return UNICODE_DATA.name[ord(chr)]
        except KeyError:
            raise ValueError('no such name')
    else:
        return UNICODE_DATA.name.get(ord(chr), default)


def category(chr: str) -> str:
    return UNICODE_DATA.category[ord(chr)]


def combining(chr: str) -> int:
    return UNICODE_DATA.combining[ord(chr)]


def block_of(chr: str) -> str:
    pass


def script_of(chr: str) -> str:
    pass
