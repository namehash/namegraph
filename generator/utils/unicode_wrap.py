def unicode_wrap(text: str) -> str:
    '''
    Encode all non-ASCII characters as their codepoints.
    All digits are encoded as well to avoid confusion with the digits in the codepoints.
    '''
    return ''.join(f'({ord(c)})' if not c.isascii() or c.isdigit() else c for c in text)
