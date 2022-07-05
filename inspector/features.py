import unicodedata
from typing import Dict, Callable

import regex
import unicodeblock.blocks
from emoji import unicode_codes
from emoji.core import emoji_count
from unidecode import unidecode

from inspector.confusables import Confusables


class Features:
    def __init__(self, config):
        self.config = config
        emojis = sorted(unicode_codes.EMOJI_DATA, key=len, reverse=True)
        emoji_pattern = u'(' + u'|'.join(regex.escape(u) for u in emojis) + u')'
        # _EMOJI_REGEXP = regex.compile(emoji_pattern)
        # EMOJI_REGEXP_AZ09 = regex.compile('^(' + emoji_pattern + '|[a-z0-9-])+$')

        self.regexp_patterns = {
            'latin-alpha': '^[a-z]+$',
            'numeric': '^[0-9]+$',
            'latin-alpha-numeric': '^[a-z0-9]+$',
            'simple': '^[a-z0-9-]+$',
            'is_emoji': emoji_pattern,
            'simple-emoji': '^(' + emoji_pattern + '|[a-z0-9-])+$',
            'is_letter': r'^\p{LC}+$',
            # TODO: is it correct? or Ll or L? include small caps http://www.unicode.org/reports/tr44/#GC_Values_Table
            'is_number': r'^\p{N}+$',  # TODO: Nd | Nl | No?
        }

        self.classes_config: Dict[str, Callable] = {
            'letter': self.is_letter,
            'number': self.is_number,
            'hyphen': self.is_hyphen,
            'emoji': self.is_emoji,
            'basic': self.simple,
            'invisible': self.invisible
        }

        self.compiled_regexp_patterns = {k: regex.compile(v) for k, v in self.regexp_patterns.items()}  # TODO: flags?

        self.script_names = [line.strip() for line in open(config.inspector.script_names)]
        self.confusables = Confusables(config)

    def length(self, name):
        """Returns number of Unicode chars in the string."""
        return len(name)

    def emoji_count(self, name):
        """Returns number of emojis in the string."""
        return emoji_count(name)

    def latin_alpha(self, name):
        """Checks if whole string matches regular expression of lowercase Latin letters."""
        return bool(self.compiled_regexp_patterns['latin-alpha'].match(name))

    def numeric(self, name):
        """Checks if whole string matches regular expression of Latin digits."""
        return bool(self.compiled_regexp_patterns['numeric'].match(name))

    def latin_alpha_numeric(self, name):
        """Checks if whole string matches regular expression of Latin lowercase letters or digits."""
        return bool(self.compiled_regexp_patterns['latin-alpha-numeric'].match(name))

    def simple(self, name):
        """Checks if whole string matches regular expression of Latin lowercase letters or digits or hyphen."""
        return bool(self.compiled_regexp_patterns['simple'].match(name))

    def is_emoji(self, name):
        """Checks if whole string matches regular expression of emojis."""
        return bool(self.compiled_regexp_patterns['is_emoji'].match(name))

    def simple_emoji(self, name):
        """Checks if whole string matches regular expression of Latin lowercase letters or digits or hyphen or 
        emojis. """
        return bool(self.compiled_regexp_patterns['simple-emoji'].match(name))

    def is_letter(self, name):
        """Checks if string matches regular expression of lowercase letters."""
        return bool(self.compiled_regexp_patterns['is_letter'].match(name))

    def is_number(self, name):
        """Checks if string matches regular expression of lowercase letters."""
        return bool(self.compiled_regexp_patterns['is_number'].match(name))

    def script_name(self, name):
        """Returns name of script (writing system) of the string, None if different scripts are used in the string."""
        result = None
        for script_name in self.script_names:
            if regex.match(r'^\p{' + script_name + r'}+$', name):
                result = script_name
                break
        return result

    def is_hyphen(self, name):
        """Detects hyphen"""
        return '-' == name

    def zwj(self, name):
        """Detects zero width joiner"""
        return '‍' == name

    def zwnj(self, name):
        """Detects zero width non-joiner"""
        return '‌' == name

    def invisible(self, name):
        """Detects zero width joiner or non-joiner"""
        return name in ('‍', '‌')

    def unicodedata_name(self, name):
        """Returns the name assigned to the character."""
        try:
            return unicodedata.name(name)
        except ValueError:
            return None

    def unicodedata_category(self, name):
        """Returns the general category assigned to the character."""
        return unicodedata.category(name)

    def unicodedata_bidirectional(self, name):
        """Returns the bidirectional class assigned to the character."""
        return unicodedata.bidirectional(name)

    def unicodedata_combining(self, name):
        """Returns the canonical combining class assigned to the character"""
        return unicodedata.combining(name)

    def unicodedata_mirrored(self, name):
        """Returns the mirrored property assigned to the character"""
        return unicodedata.mirrored(name)

    def unicodedata_decomposition(self, name):
        """Returns the character decomposition mapping assigned to the character"""
        return unicodedata.decomposition(name)

    def unicodeblock(self, name):
        """Return a name of Unicode block in which the character is."""
        return unicodeblock.blocks.of(name)

    def is_confusable(self, name):
        """Indicates if a character is confusable."""
        return self.confusables.is_confusable(name)

    def get_confusables(self, name):
        """Return set of confusable characters."""
        return self.confusables.get_confusables(name)

    def get_canonical(self, name):
        """Returns canonical character from confusable set."""
        return self.confusables.get_canonical(name)

    def is_ascii(self, name):
        """Detects if name is all ASCII."""
        try:
            name.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def codepoint(self, name):
        """Codepoint of Unicode char as hex with 0x prefix."""
        return f'{ord(name):x}'

    def codepoint_int(self, name):
        """Codepoint of Unicode char as integer."""
        return ord(name)

    def codepoint_hex(self, name):
        """Codepoint of Unicode char as hex."""
        return hex(ord(name))

    def link(self, name):
        """Link to external page with Unicode character information."""
        return f'https://unicode.link/codepoint/{ord(name):x}'

    def name(self, name):
        return name

    def bytes(self, name):
        """Number of bytes in UTF8 encoding."""
        return len(name.encode('utf-8'))

    def unidecode(self, name):
        """https://pypi.org/project/Unidecode/ Tries to represent name in ASCII characters.
        It converts 'ł' to 'l', 'ω' (omega) to 'o'.
        """
        return unidecode(name, errors='ignore')

    def NFKD_ascii(self, name):
        """Returns string after decomposition in compatible mode with removed non-ascii chars."""
        return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')

    def NFD_ascii(self, name):
        """Returns string after decomposition with removed non-ascii chars."""
        return unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')

    def NFKD(self, name):
        """Returns string after decomposition in compatible mode."""
        return unicodedata.normalize('NFKD', name)

    def NFD(self, name):
        """Returns string after decomposition."""
        return unicodedata.normalize('NFD', name)

    def classes(self, name):
        """Return classes of string: letter,number,hyphen,emoji,basic,invisible"""
        result = []
        for c, func in self.classes_config.items():
            if func(name):
                result.append(c)
        return tuple(result)  # TODO
