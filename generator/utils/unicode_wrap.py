# allow all ASCII characters except digits and parentheses (which are used for encoding)
ALLOWED_CHARS = set(c for c in (chr(i) for i in range(256)) if c.isascii() and not c.isdigit() and c not in ('(', ')'))


def unicode_wrap(text: str) -> str:
    '''
    Encode all non-ASCII characters as their codepoints - "ą" -> "(261)".
    All digits and parentheses are encoded as well to avoid confusion with the encodings.
    '''
    return ''.join(f'({ord(c)})' if c not in ALLOWED_CHARS else c for c in text)
