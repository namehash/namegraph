from .utils import load_ranges
from bisect import bisect_right


def _load_emoji_ranges():
    starts, names = load_ranges('data/myunicode/emoji-ranges.txt')
    is_emoji = [name is not None for name in names]
    return starts, is_emoji


_EMOJI_STARTS, _IS_EMOJI = _load_emoji_ranges()


def char_is_emoji(chr: str) -> bool:
    return _IS_EMOJI[bisect_right(_EMOJI_STARTS, ord(chr)) - 1]
