import unicodedata
from typing import Dict, Callable, Union, List, Iterable

import regex
import spacy
import ens
import idna
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

        self.regexp_patterns = {
            'simple_letter': '^[a-z]+$',
            'numeric': '^[0-9]+$',
            'latin-alpha-numeric': '^[a-z0-9]+$',
            'simple': '^[a-z0-9-]+$',
            'is_emoji': '^(' + emoji_pattern + ')+$',
            'simple-emoji': '^([a-z0-9-]|' + emoji_pattern + ')+$',
            'simple_letter-emoji': '^([a-z]|' + emoji_pattern + ')+$',
            'is_letter': r'^(\p{Ll}|\p{Lu}|\p{Lt}|\p{Lo})+$',  # \p{LC} not work properly in regex
            # TODO: is it correct? or Ll or L? include small caps http://www.unicode.org/reports/tr44/#GC_Values_Table
            'is_number': r'^\p{N}+$',  # TODO: replace with numeric data from Unicode.org
        }

        self.classes_config: Dict[str, Callable] = {
            'any_letter': self.is_letter,
            'any_number': self.simple_number,
            'hyphen': self.is_hyphen,
            'emoji': self.is_emoji,
            'simple': self.simple,
            'invisible': self.invisible,
            'simple_letter': self.simple_letter,
            'simple_number': self.simple_number,
            'simple_letter_emoji': self.simple_letter_emoji,
            # 'other_letter': self.other_letter,
            # 'other_number': self.other_number,
        }
        self.token_classes_config: Dict[str, Callable] = {
            'any_letter': self.is_letter,
            'any_number': self.simple_number,
            'hyphen': self.is_hyphen,
            'emoji': self.is_emoji,
            'simple': self.simple,
            'invisible': self.invisible,
            'simple_letter': self.simple_letter,
            'simple_number': self.simple_number,
            # 'other_letter': self.other_letter,
            # 'other_number': self.other_number,
        }

        self.char_classes_config: Dict[str, Callable] = {
            'simple_letter': self.simple_letter,
            'simple_number': self.simple_number,
            'any_letter': self.is_letter,
            'any_number': self.is_number,
            'hyphen': self.is_hyphen,
            'emoji': self.is_emoji,
            'invisible': self.invisible,
        }

        self.compiled_regexp_patterns = {k: regex.compile(v) for k, v in self.regexp_patterns.items()}  # TODO: flags?

        self.script_names = [line.strip() for line in open(config.inspector.script_names)]
        self.compiled_script_names = {script_name: regex.compile(r'^\p{' + script_name + r'}+$') for script_name in
                                      self.script_names}

        self.confusables = Confusables(config)

        self.nlp = spacy.load('en_core_web_sm')

        self.dictionary = set()
        skip_one_letter_words = config.tokenization.skip_one_letter_words
        with open(config.tokenization.dictionary) as f:
            for line in f:
                word = line.strip().lower()
                if skip_one_letter_words and len(word) == 1: continue
                self.dictionary.add(word)
        if config.tokenization.add_letters_ias:
            for char in 'ias':
                self.dictionary.add(char)

    def length(self, name) -> int:
        """Returns number of Unicode chars in the string."""
        return len(name)

    def emoji_count(self, name) -> int:
        """Returns number of emojis in the string."""
        return emoji_count(name)

    def simple_letter(self, name) -> bool:
        """Checks if whole string matches regular expression of lowercase Latin letters."""
        return bool(self.compiled_regexp_patterns['simple_letter'].match(name))

    def simple_letter_emoji(self, name) -> bool:  # TODO: slow
        """Checks if whole string matches regular expression of lowercase Latin letters."""
        return bool(self.compiled_regexp_patterns['simple_letter-emoji'].match(name))

    def numeric(self, name) -> bool:
        """Checks if whole string matches regular expression of Latin digits."""
        return bool(self.compiled_regexp_patterns['numeric'].match(name))

    def latin_alpha_numeric(self, name) -> bool:
        """Checks if whole string matches regular expression of Latin lowercase letters or digits."""
        return bool(self.compiled_regexp_patterns['latin-alpha-numeric'].match(name))

    def simple(self, name) -> bool:
        """Checks if whole string matches regular expression of Latin lowercase letters or digits or hyphen."""
        return bool(self.compiled_regexp_patterns['simple'].match(name))

    def is_emoji(self, name) -> bool:
        """Checks if whole string matches regular expression of emojis."""
        return bool(self.compiled_regexp_patterns['is_emoji'].match(name))

    def simple_emoji(self, name) -> bool:
        """Checks if whole string matches regular expression of Latin lowercase letters or digits or hyphen or 
        emojis. """
        return bool(self.compiled_regexp_patterns['simple-emoji'].match(name))

    def is_letter(self, name) -> bool:
        """Checks if string matches regular expression of lowercase letters."""
        return bool(self.compiled_regexp_patterns['is_letter'].match(name))

    def simple_number(self, name) -> bool:
        """Checks if string matches regular expression of lowercase letters."""
        return bool(self.compiled_regexp_patterns['is_number'].match(name))

    def is_number(self, name) -> bool:
        return False  # TODO

    def script_name(self, name) -> Union[str, None]:  # TODO does it need to depend on script names? 
        """Returns name of script (writing system) of the string, None if different scripts are used in the string."""
        result = None
        for script_name, regexp in self.compiled_script_names.items():  # TODO: slow
            if regexp.match(name):
                result = script_name
                break
        return result

    def is_hyphen(self, name) -> bool:
        """Detects hyphen"""
        return '-' == name

    def zwj(self, name) -> bool:
        """Detects zero width joiner"""
        return '\u200d' == name  # '‍'

    def zwnj(self, name) -> bool:
        """Detects zero width non-joiner"""
        return '\u200c' == name  # '‌'

    def invisible(self, name) -> bool:
        """Detects zero width joiner or non-joiner"""
        return name in ('\u200d', '\u200c')  # ('‍', '‌')

    def unicodedata_name(self, name) -> Union[str, None]:
        """Returns the name assigned to the character."""
        try:
            return unicodedata.name(name)
        except ValueError:
            return None

    def unicodedata_category(self, name) -> str:
        """Returns the general category assigned to the character: http://www.unicode.org/reports/tr44/#GC_Values_Table"""
        return unicodedata.category(name)

    def unicodedata_bidirectional(self, name) -> str:
        """Returns the bidirectional class assigned to the character or empty string."""
        return unicodedata.bidirectional(name)

    def unicodedata_combining(self, name) -> int:
        """Returns the canonical combining class assigned to the character. Returns 0 if no combining class is defined.."""
        return unicodedata.combining(name)

    def unicodedata_mirrored(self, name) -> int:
        """Returns the mirrored property assigned to the character"""
        return unicodedata.mirrored(name)

    def unicodedata_decomposition(self, name) -> str:
        """Returns the character decomposition mapping assigned to the character"""
        return unicodedata.decomposition(name)

    def unicodeblock(self, name) -> Union[str, None]:
        """Return a name of Unicode block in which the character is or None"""
        return unicodeblock.blocks.of(name)

    def is_confusable(self, name) -> bool:
        """Indicates if a character is confusable."""
        return self.confusables.is_confusable(name)

    def get_confusables(self, name) -> Iterable[str]:
        """Return set of confusable characters."""
        return self.confusables.get_confusables(name)

    def get_canonical(self, name):
        """Returns canonical character from confusable set."""
        return self.confusables.get_canonical(name)

    def is_ascii(self, name) -> bool:
        """Detects if name is all ASCII."""
        try:
            name.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def codepoint(self, name) -> str:
        """Codepoint of Unicode char as hex with 0x prefix."""
        return f'{ord(name):x}'

    def codepoint_int(self, name) -> int:
        """Codepoint of Unicode char as integer."""
        return ord(name)

    def codepoint_hex(self, name) -> str:
        """Codepoint of Unicode char as hex."""
        return hex(ord(name))

    def link(self, name) -> str:
        """Link to external page with Unicode character information."""
        return f'https://unicode.link/codepoint/{ord(name):x}'

    def name(self, name) -> str:
        return name

    def in_dictionary(self, name) -> bool:
        """Checks if string is in dictionary."""
        return name in self.dictionary

    def bytes(self, name) -> int:
        """Number of bytes in UTF8 encoding."""
        return len(name.encode('utf-8'))

    def unidecode(self, name) -> str:
        """https://pypi.org/project/Unidecode/ Tries to represent name in ASCII characters.
        It converts 'ł' to 'l', 'ω' (omega) to 'o'.
        """
        return unidecode(name, errors='ignore')

    def NFKD_ascii(self, name) -> str:
        """Returns string after decomposition in compatible mode with removed non-ascii chars."""
        return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')

    def NFD_ascii(self, name) -> str:
        """Returns string after decomposition with removed non-ascii chars."""
        return unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')

    def NFKD(self, name) -> str:
        """Returns string after decomposition in compatible mode."""
        return unicodedata.normalize('NFKD', name)

    def NFD(self, name) -> str:
        """Returns string after decomposition."""
        return unicodedata.normalize('NFD', name)

    def classes(self, name) -> List[str]:
        """Return classes of string: letter,number,hyphen,emoji,simple,invisible"""
        result = []
        for c, func in self.classes_config.items():
            if func(name):
                result.append(c)
        return result

    def token_classes(self, name) -> List[str]:
        """Return classes of string: letter,number,hyphen,emoji,simple,invisible"""
        result = []
        for c, func in self.token_classes_config.items():
            if func(name):
                result.append(c)
        return result

    def char_class(self, name) -> str:
        """Return classes of char: simple_letter,simple_number,any_letter,any_number,hyphen,emoji,invisible,special"""
        for c, func in self.char_classes_config.items():
            if func(name):
                return c
        return 'special'

    def ens_is_valid_name(self, name) -> bool:
        return ens.main.ENS.is_valid_name(name)

    def ens_nameprep(self, name) -> Union[str, None]:
        try:
            nameprep = ens.main.ENS.nameprep(name)
        except ens.exceptions.InvalidName:
            nameprep = None
        return nameprep

    def uts46_remap(self, name) -> Union[str, None]:
        try:
            uts46_remap = idna.uts46_remap(name, std3_rules=True, transitional=False)
        except idna.core.InvalidCodepoint:
            uts46_remap = None
        return uts46_remap

    def idna_encode(self, name) -> Union[str, None]:
        try:
            encode = idna.encode(name, uts46=True, std3_rules=True, transitional=False)
        except idna.core.InvalidCodepoint:
            encode = None
        except idna.core.IDNAError as e:
            encode = None
        return encode
