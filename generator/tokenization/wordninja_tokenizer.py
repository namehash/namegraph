import re
from typing import List, Tuple
from functools import lru_cache
import wordninja
import emoji
from emoji import EmojiMatch

from .tokenizer import Tokenizer

_SPLIT_RE = re.compile("([a-zA-Z0-9']+|\d+)", re.UNICODE)
_SIMPLE_RE = re.compile("^[a-zA-Z0-9']+$")

def emoji_split(name: str) -> List[Tuple[str, bool]]:
    token = []
    for c in emoji.tokenizer.tokenize(name, keep_zwj=True):
        if isinstance(c.value, EmojiMatch):
            if token:
                yield ''.join(token), False
                token = []
            yield c.chars, True
        else:
            token.append(c.chars)
    if token:
        yield ''.join(token), False

@lru_cache(64)
def _tokenizer(name: str) -> List[Tuple[str, ...]]:
    tokens = []
    for token, is_emoji in emoji_split(name):
        if is_emoji:
            tokens.append(token)
        else:
            split_name = _SPLIT_RE.split(token)
            for token2 in split_name:
                if not token2:
                    continue
                if _SIMPLE_RE.match(token2):
                    tokens.extend(wordninja.split(token2))
                else:
                    tokens.append(token2)
    return [tuple(tokens)]


class WordNinjaTokenizer(Tokenizer):
    """Return one the most probable tokenization."""

    def __init__(self, config):
        super().__init__()
        wordninja.DEFAULT_LANGUAGE_MODEL = wordninja.LanguageModel(config.tokenization.wordninja_dictionary)

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        return _tokenizer(name)
