from .data import UNICODE_DATA
from .blocks import BLOCK_STARTS, BLOCK_NAMES
from .scripts import script_of_char, NEUTRAL_SCRIPTS
from .emojis import EMOJI_STARTS, IS_EMOJI

from bisect import bisect_right
from typing import Optional


def name(chr: str, default=None) -> str:
    """
    Returns the name of the unicode character.
    If the character does not have a name,
    returns default if given or throws an exception.
    """
    if len(chr) != 1:
        raise TypeError('name() argument 1 must be a unicode character, not str')
    try:
        return UNICODE_DATA.name(ord(chr))
    except KeyError:
        if default is None:
            raise ValueError('no such name')
        return default


def category(chr: str) -> str:
    """
    Returns the category of the unicode character.
    If the character does not have a category, returns 'Cn'.
    """
    if len(chr) != 1:
        raise TypeError('category() argument must be a unicode character, not str')
    try:
        return UNICODE_DATA.category(ord(chr))
    except KeyError:
        return 'Cn'


def combining(chr: str) -> int:
    """
    Returns the combining class of the unicode character.
    If the character does not have a combining class, returns 0.
    """
    if len(chr) != 1:
        raise TypeError('combining() argument must be a unicode character, not str')
    try:
        return UNICODE_DATA.combining(ord(chr))
    except KeyError:
        return 0


def block_of(chr: str) -> str:
    """
    Returns the block of the character.
    If the character does not have a block, throws exception.
    """
    if len(chr) != 1:
        raise TypeError('block_of() argument must be a unicode character, not str')
    return BLOCK_NAMES[bisect_right(BLOCK_STARTS, ord(chr)) - 1]


def script_of(text: str) -> Optional[str]:
    """
    Returns the script of text, or None if text has many scripts.
    Common, Inherited and Unknown scripts are considered neutral.
    Returns None if text has only neutral scripts.
    """
    script = None

    for c in text:
        s = script_of_char(c)

        if s in NEUTRAL_SCRIPTS:
            continue

        if script is None:
            # found first non-neutral character
            script = s
        elif script != s:
            # conflict
            return None

    return script


def is_emoji(chr: str) -> bool:
    """
    Returns True if the character is an emoji.
    """
    if len(chr) != 1:
        raise TypeError('is_emoji() argument must be a unicode character, not str')
    return IS_EMOJI[bisect_right(EMOJI_STARTS, ord(chr)) - 1]


def is_numeric(chr: str) -> bool:
    """
    Returns True if the character is numeric (category N).
    """
    if len(chr) != 1:
        raise TypeError('is_numeric() argument must be a unicode character, not str')
    return category(chr).startswith('N')
