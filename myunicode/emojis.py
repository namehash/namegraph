from .utils import load_ranges


def _load_emoji_ranges():
    starts, names = load_ranges('data/myunicode/emoji-ranges.txt')
    # name is either None (not emoji range) or empty string (is emoji range)
    is_emoji = [name is not None for name in names]
    return starts, is_emoji


EMOJI_STARTS, IS_EMOJI = _load_emoji_ranges()
