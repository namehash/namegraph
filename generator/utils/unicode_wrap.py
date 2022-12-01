def unicode_wrap(text: str) -> str:
    if len(text) == 0:
        return ''
    return '|' + '|'.join(f'{ord(c):x}' for c in text) + '|'


def unicode_unwrap(text: str) -> str:
    if len(text) == 0:
        return ''
    return ''.join(chr(int(c, 16)) for c in text[1:-1].split('|'))
