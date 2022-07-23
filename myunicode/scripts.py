from .utils import load_ranges
from bisect import bisect_right


_SCRIPT_STARTS, _SCRIPT_NAMES = load_ranges('data/myunicode/Scripts.txt')


def script_of_char(chr: str) -> str:
    script = _SCRIPT_NAMES[bisect_right(_SCRIPT_STARTS, ord(chr)) - 1]
    return script if script is not None else 'Unknown'
