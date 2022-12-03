def unicode_wrap(text: str) -> str:
    return ''.join(f'({ord(c)})' if ord(c) > 127 else c for c in text)
