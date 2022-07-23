from .utils import load_ranges


def _load_emoji_ranges():
    starts, names = load_ranges('data/myunicode/emoji-ranges.txt')
    is_emoji = [name is not None for name in names]
    return starts, is_emoji


EMOJI_STARTS, IS_EMOJI = _load_emoji_ranges()
