import json
import re
import unicodedata
from typing import Tuple, Iterator

from name_graph.generation import NameGenerator
from ..input_name import InputName, Interpretation
from name_graph.thread_utils import get_random_rng


class RhymesGenerator(NameGenerator):
    """
    Yields names rhyming with the name.
    """

    def __init__(self, config):
        super().__init__(config)
        with open(config.generation.suffix2rhymes_path, 'r', encoding='utf-8') as f:
            self.suffix2rhymes = json.load(f)
        self.to_vowel_metaphone = lambda s: vowel_metaphone(s)[1][0]


    def generate(self, tokens: Tuple[str, ...]) -> Iterator[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        name = ''.join(tokens)

        if len(name) < 3 or not name.isalpha() or not any([c.upper() in VOWELS for c in name]):
            return []

        name_vmetaphone_repr = self.to_vowel_metaphone(name)
        if len(name_vmetaphone_repr) < 3 or not any([c in VOWELS for c in name_vmetaphone_repr]):
            return []

        rhyme_suffix = RhymesGenerator.get_rhyme_suffix(name_vmetaphone_repr)

        rng = get_random_rng()

        for suffix_len in range(len(rhyme_suffix), 2, -1):
            suffix = rhyme_suffix[-suffix_len:]
            rhymes = self.suffix2rhymes.get(suffix, None)
            if rhymes is None:
                continue

            # shuffle rhymes
            rhymes_len = len(rhymes)
            if rhymes_len > 50:
                shuffle_threshold = 20
            elif rhymes_len > 25:
                shuffle_threshold = 10
            elif rhymes_len > 10:
                shuffle_threshold = 5
            else:
                shuffle_threshold = rhymes_len // 2

            rhymes_top = rhymes[:shuffle_threshold]
            rhymes_bottom = rhymes[shuffle_threshold:]
            rng.shuffle(rhymes_top)
            rng.shuffle(rhymes_bottom)
            rhymes = rhymes_top + rhymes_bottom

            try:
                yield from [(name, r) for r in rhymes if r != name and r not in tokens]
            except StopIteration:
                continue


    def generate2(self, name: InputName, interpretation: Interpretation) -> Iterator[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))


    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}


    @staticmethod
    def get_rhyme_suffix(s_vmet: str) -> str:
        assert len(s_vmet) >= 3
        if len(s_vmet) == 3:
            return s_vmet

        vowel_positions = [match.start() for match in re.finditer(r'[AEIOUY]', s_vmet)]
        if len(vowel_positions) == 1 and vowel_positions[0] != len(s_vmet) - 1:
            suf = s_vmet[vowel_positions[0]:]
            if len(suf) >= 3:
                return suf  # ex.: czad [SAT | XAT] -> SAT, smith [SMI0 | XMIT] -> MI0
            else:
                return s_vmet[-3:]
        elif (len(vowel_positions) == 1 and vowel_positions[0] != len(s_vmet) - 1) or \
                len(vowel_positions) > 1:
            suf = s_vmet[vowel_positions[-1] - 1:]
            if len(suf) >= 3:
                return suf  # ex.: crew [KRE] -> KRE, affair [AFAIR] -> AIR, salmon [SALMON] -> MON
            else:
                return s_vmet[-3:]
        else:
            return ''  # no rhymes for string without vowels


# ========== VOWEL METAPHONE ==========

VOWELS = ['A', 'E', 'I', 'O', 'U', 'Y']
SILENT_STARTERS = ["GN", "KN", "PN", "WR", "PS"]


class MetaphoneWord:
    def __init__(self, input_str):
        self.original = input_str
        self.decoded = input_str
        self.decoded = self.decoded.replace('\xc7', "s")
        self.decoded = self.decoded.replace('\xe7', "s")
        self.normalized = ''.join(
            (c for c in unicodedata.normalize('NFD', self.decoded)
             if unicodedata.category(c) != 'Mn'))
        self.upper = self.normalized.upper()
        self.length = len(self.upper)
        self.prepad = "  "
        self.start_index = len(self.prepad)
        self.end_index = self.start_index + self.length - 1
        self.postpad = "      "
        # so we can index beyond the beginning and end of the input string
        self.buffer = self.prepad + self.upper + self.postpad

    @property
    def is_slavo_germanic(self):
        return (
                self.upper.find('W') > -1
                or self.upper.find('K') > -1
                or self.upper.find('CZ') > -1
                or self.upper.find('WITZ') > -1)

    def get_letters(self, start=0, end=None):
        if not end:
            end = start + 1
        start = self.start_index + start
        end = self.start_index + end
        return self.buffer[start:end]


class VowelMetaphone:

    def __init__(self):
        self.position = 0
        self.primary_phone = ""
        self.secondary_phone = ""
        # next is used set to a tuple of the next characters in the primary and
        # secondary codes and to indicate how many characters to move forward
        # in the string.  The secondary code letter is given only when it is
        # different from the primary. This is just a trick to make the code
        # easier to write and read. The default action is to add nothing and
        # move to next char.
        self.next = (None, 1)
        self.word = None

        self.primary_phone_with_vowels = ''
        self.secondary_phone_with_vowels = ''
        self.next_vowel = None

    def check_word_start(self):
        # skip these silent letters when at start of word
        if self.word.get_letters(0, 2) in SILENT_STARTERS:
            self.position += 1
        # Initial 'X' is pronounced 'Z' e.g. 'Xavier'
        if self.word.get_letters(0) == 'X':
            # 'Z' maps to 'S'
            self.primary_phone = self.secondary_phone = 'S'
            self.primary_phone_with_vowels = self.secondary_phone_with_vowels = 'S'
            self.position += 1

    def process_vowels(self, ch):
        self.next = (None, 1)
        if self.position == self.word.start_index:
            self.next = (ch, 1)

        # preserving vowels
        self.next_vowel = ch

        # skipping if triple or more, double vowels should be preserved or collapsed to a single vowel
        if self.word.buffer[self.position + 1] == ch and self.word.buffer[self.position + 2] == ch:
            self.next_vowel = None

        # todo: collapse some vowel pairs into a single vowel?
        # but: collapsing vowel pairs could actually worsen the rhyme matching
        # (English vowels' phones are very irregular)
        #  'ai', 'ay', 'ee', 'ea', 'ie', 'ei', 'oo', 'ou', 'oy', 'oa', 'oi'

        # if ch == 'O' and self.word.buffer[self.position - 1] == 'O' and \
        #         self.word.buffer[self.position + 1] != 'O':  # OO
        #     if self.word.buffer[self.position - 2] == 'L' and self.word.buffer[self.position + 1] == 'D':  # BLOOD
        #         self.primary_phone_with_vowels = self.primary_phone_with_vowels[:-1] + 'A'
        #         self.secondary_phone_with_vowels = self.secondary_phone_with_vowels[:-1] + 'A'
        #         self.next_vowel = None
        #     elif self.word.buffer[self.position + 2] == 'R':  # DOOR
        #         self.primary_phone_with_vowels = self.primary_phone_with_vowels[:-1] + 'O'
        #         self.secondary_phone_with_vowels = self.secondary_phone_with_vowels[:-1] + 'O'
        #         self.next_vowel = None
        #     else:  # MOON
        #         self.primary_phone_with_vowels = self.primary_phone_with_vowels[:-1] + 'U'
        #         self.secondary_phone_with_vowels = self.secondary_phone_with_vowels[:-1] + 'U'
        #         self.next_vowel = None

    def process_b(self):
        # "-mb", e.g., "dumb", already skipped over... see 'M' below
        if self.word.buffer[self.position + 1] == 'B':
            self.next = ('P', 2)
        else:
            self.next = ('P', 1)

    def process_c(self):
        buffer = self.word.buffer
        position = self.position
        start_index = self.word.start_index
        # various germanic
        if (position > start_index + 1
                and buffer[position - 2] not in VOWELS
                and buffer[position - 1:self.position + 2] == 'ACH'
                and buffer[position + 2] not in ['I']
                and (buffer[position + 2] not in ['E']
                     or buffer[position - 2:position + 4] in [
                         'BACHER', 'MACHER'])):
            self.next = ('K', 2)
        # special case 'CAESAR'
        elif (position == start_index
              and buffer[start_index:start_index + 6] == 'CAESAR'):
            self.next = ('S', 2)
        # italian 'chianti'
        elif buffer[position:position + 4] == 'CHIA':
            self.next = ('K', 2)
        elif buffer[position:position + 2] == 'CH':
            # find 'michael'
            if (position > start_index
                    and buffer[position:position + 4] == 'CHAE'):
                self.next = ('K', 'X', 2)
            elif (position == start_index
                  and (buffer[position + 1:position + 6] in ['HARAC', 'HARIS']
                       or buffer[position + 1:position + 4] in ["HOR", "HYM", "HIA",
                                                                "HEM"])
                  and buffer[start_index:start_index + 5] != 'CHORE'):
                self.next = ('K', 2)
            # germanic, greek, or otherwise 'ch' for 'kh' sound
            elif (
                    buffer[start_index:start_index + 4] in ['VAN ', 'VON ']
                    or buffer[start_index:start_index + 3] == 'SCH'
                    or buffer[position - 2:position + 4] in ["ORCHES", "ARCHIT",
                                                             "ORCHID"]
                    or buffer[position + 2] in ['T', 'S']
                    or (
                            (buffer[position - 1] in ["A", "O", "U", "E"]
                             or position == start_index)
                            and (buffer[position + 2] in ["L", "R", "N", "M", "B", "H", "F", "V", "W", " "]))):
                self.next = ('K', 2)
            else:
                if position > start_index:
                    if buffer[start_index:start_index + 2] == 'MC':
                        self.next = ('K', 2)
                    else:
                        self.next = ('X', 'K', 2)
                else:
                    self.next = ('X', 2)
        # e.g, 'czerny'
        elif (buffer[position:position + 2] == 'CZ'
              and buffer[position - 2:position + 2] != 'WICZ'):
            self.next = ('S', 'X', 2)
        # e.g., 'focaccia'
        elif buffer[position + 1:position + 4] == 'CIA':
            self.next = ('X', 3)
        # double 'C', but not if e.g. 'McClellan'
        elif (
                buffer[position:position + 2] == 'CC'
                and not (position == (start_index + 1)
                         and buffer[start_index] == 'M')):
            # 'bellocchio' but not 'bacchus'
            if (buffer[position + 2] in ["I", "E", "H"]
                    and buffer[position + 2:position + 4] != 'HU'):
                # 'accident', 'accede' 'succeed'
                if ((position == (start_index + 1) and
                     buffer[start_index] == 'A') or
                        buffer[position - 1:position + 4] in ['UCCEE', 'UCCES']):
                    self.next = ('KS', 3)
                # 'bacci', 'bertucci', other italian
                else:
                    self.next = ('X', 3)
            else:
                self.next = ('K', 2)
        elif buffer[position:position + 2] in ["CK", "CG", "CQ"]:
            self.next = ('K', 2)
        elif buffer[position:position + 2] in ["CI", "CE", "CY"]:
            # italian vs. english
            if buffer[position:position + 3] in ["CIO", "CIE", "CIA"]:
                self.next = ('S', 'X', 2)
            else:
                self.next = ('S', 2)
        else:
            # name sent in 'mac caffrey', 'mac gregor'
            if buffer[position + 1:position + 3] in [" C", " Q", " G"]:
                self.next = ('K', 3)
            else:
                if (buffer[position + 1] in ["C", "K", "Q"]
                        and buffer[position + 1:position + 3] not in ["CE", "CI"]):
                    self.next = ('K', 2)
                # default for 'C'
                else:
                    self.next = ('K', 1)

    def process_d(self):
        if self.word.buffer[self.position:self.position + 2] == 'DG':
            # e.g. 'edge'
            if self.word.buffer[self.position + 2] in ['I', 'E', 'Y']:
                self.next = ('J', 3)
            else:
                self.next = ('TK', 2)
        elif self.word.buffer[self.position:self.position + 2] in ['DT', 'DD']:
            self.next = ('T', 2)
        else:
            self.next = ('T', 1)

    def process_f(self):
        if self.word.buffer[self.position + 1] == 'F':
            self.next = ('F', 2)
        else:
            self.next = ('F', 1)

    def process_g(self):
        buffer = self.word.buffer
        position = self.position
        start_index = self.word.start_index
        if buffer[position + 1] == 'H':
            if (position > start_index
                    and buffer[position - 1] not in VOWELS):
                self.next = ('K', 2)
            elif position < (start_index + 3):
                # 'ghislane', ghiradelli
                if position == start_index:
                    if buffer[position + 2] == 'I':
                        self.next = ('J', 2)
                    else:
                        self.next = ('K', 2)
            # Parker's rule (with some further refinements) - e.g., 'hugh'
            elif (
                    (position > (start_index + 1)
                     and buffer[position - 2] in ['B', 'H', 'D'])
                    or (position > (start_index + 2)
                        and buffer[position - 3] in ['B', 'H', 'D'])
                    or (position > (start_index + 3)
                        and buffer[position - 4] in ['B', 'H'])):
                self.next = (None, 2)
            else:
                # e.g., 'laugh', 'McLaughlin', 'cough', 'gough', 'rough',
                # 'tough'
                if (position > (start_index + 2)
                        and buffer[position - 1] == 'U'
                        and buffer[position - 3] in [
                            "C", "G", "L", "R", "T"]):
                    self.next = ('F', 2)
                else:
                    if (position > start_index
                            and buffer[position - 1] != 'I'):
                        self.next = ('K', 2)
        elif buffer[position + 1] == 'N':
            if (position == (start_index + 1)
                    and buffer[start_index] in VOWELS
                    and not self.word.is_slavo_germanic):
                self.next = ('KN', 'N', 2)
            else:
                # not e.g. 'cagney'
                if (buffer[position + 2:position + 4] != 'EY'
                        and buffer[position + 1] != 'Y'
                        and not self.word.is_slavo_germanic):
                    self.next = ('N', 'KN', 2)
                else:
                    self.next = ('KN', 2)
        # 'tagliaro'
        elif (buffer[position + 1:position + 3] == 'LI'
              and not self.word.is_slavo_germanic):
            self.next = ('KL', 'L', 2)
        # -ges-,-gep-,-gel-, -gie- at beginning
        elif (position == start_index
              and (buffer[position + 1] == 'Y'
                   or buffer[position + 1:position + 3] in [
                       "ES", "EP", "EB", "EL", "EY", "IB", "IL", "IN", "IE", "EI",
                       "ER"])):
            self.next = ('K', 'J', 2)
        # -ger-,  -gy-
        elif (
                (buffer[position + 1:position + 3] == 'ER'
                 or buffer[position + 1] == 'Y')
                and buffer[start_index:start_index + 6] not in [
                    "DANGER", "RANGER", "MANGER"]
                and buffer[position - 1] not in ['E', 'I']
                and buffer[position - 1:position + 2] not in ['RGY', 'OGY']):
            self.next = ('K', 'J', 2)
        # italian e.g, 'biaggi'
        elif (
                buffer[position + 1] in ['E', 'I', 'Y']
                or buffer[position - 1:position + 3] in [
                    "AGGI", "OGGI"]):
            # obvious germanic
            if (buffer[start_index:start_index + 4] in ['VON ', 'VAN ']
                    or buffer[start_index:start_index + 3] == 'SCH'
                    or buffer[position + 1:position + 3] == 'ET'):
                self.next = ('K', 2)
            else:
                # always soft if french ending
                if buffer[position + 1:position + 5] == 'IER ':
                    self.next = ('J', 2)
                else:
                    self.next = ('J', 'K', 2)
        elif buffer[position + 1] == 'G':
            self.next = ('K', 2)
        else:
            self.next = ('K', 1)

    def process_h(self):
        # only keep if self.word.start_index & before vowel or btw. 2 vowels
        if ((self.position == self.word.start_index
             or self.word.buffer[self.position - 1] in VOWELS)
                and self.word.buffer[self.position + 1] in VOWELS):
            self.next = ('H', 2)
        # (also takes care of 'HH')
        else:
            self.next = (None, 1)

    def process_j(self):
        buffer = self.word.buffer
        position = self.position
        start_index = self.word.start_index
        # obvious spanish, 'jose', 'san jacinto'
        if (buffer[self.position:self.position + 4] == 'JOSE'
                or buffer[start_index:start_index + 4] == 'SAN '):
            if (
                    (position == start_index and buffer[position + 4] == ' ')
                    or buffer[start_index:start_index + 4] == 'SAN '):
                self.next = ('H',)
            else:
                self.next = ('J', 'H')
        # Yankelovich/Jankelowicz
        elif (position == start_index
              and buffer[self.position:self.position + 4] != 'JOSE'):
            self.next = ('J', 'A')
        else:
            # spanish pron. of e.g. 'bajador'
            if (buffer[position - 1] in VOWELS
                    and not self.word.is_slavo_germanic
                    and buffer[position + 1] in ['A', 'O']):
                self.next = ('J', 'H')
            else:
                if position == self.word.end_index:
                    self.next = ('J', ' ')
                else:
                    if (buffer[position + 1] not in ["L", "T", "K", "S", "N",
                                                     "M", "B", "Z"]
                            and buffer[position - 1] not in ["S", "K", "L"]):
                        self.next = ('J',)
                    else:
                        self.next = (None,)
        if buffer[position + 1] == 'J':
            self.next = self.next + (2,)
        else:
            self.next = self.next + (1,)

    def process_k(self):
        if self.word.buffer[self.position + 1] == 'K':
            self.next = ('K', 2)
        else:
            self.next = ('K', 1)

    def process_l(self):
        buffer = self.word.buffer
        position = self.position
        end_index = self.word.end_index
        if buffer[position + 1] == 'L':
            # spanish e.g. 'cabrillo', 'gallegos'
            if ((position == (end_index - 2)
                 and buffer[position - 1:position + 3] in [
                     "ILLO", "ILLA", "ALLE"])
                    or ((buffer[end_index - 1:end_index + 1] in ["AS", "OS"]
                         or buffer[end_index] in ["A", "O"])
                        and buffer[position - 1:position + 3] == 'ALLE')):
                self.next = ('L', '', 2)
            else:
                self.next = ('L', 2)
        else:
            self.next = ('L', 1)

    def process_m(self):
        buffer = self.word.buffer
        position = self.position
        if ((buffer[position + 1:position + 4] == 'UMB'
             and (position + 1 == self.word.end_index
                  or buffer[position + 2:position + 4] == 'ER'))
                or buffer[position + 1] == 'M'):
            self.next = ('M', 2)
        else:
            self.next = ('M', 1)

    def process_n(self):
        if self.word.buffer[self.position + 1] == 'N':
            self.next = ('N', 2)
        else:
            self.next = ('N', 1)

    def process_p(self):
        if self.word.buffer[self.position + 1] == 'H':
            self.next = ('F', 2)
        # also account for "campbell", "raspberry"
        elif self.word.buffer[self.position + 1] in ['P', 'B']:
            self.next = ('P', 2)
        else:
            self.next = ('P', 1)

    def process_q(self):
        if self.word.buffer[self.position + 1] == 'Q':
            self.next = ('K', 2)
        else:
            self.next = ('K', 1)

    def process_r(self):
        buffer = self.word.buffer
        position = self.position
        end_index = self.word.end_index
        # french e.g. 'rogier', but exclude 'hochmeier'
        if (position == end_index
                and not self.word.is_slavo_germanic
                and buffer[position - 2:position] == 'IE'
                and buffer[position - 4:position - 2] not in ['ME', 'MA']):
            self.next = ('', 'R')
        else:
            self.next = ('R',)
        if buffer[position + 1] == 'R':
            self.next = self.next + (2,)
        else:
            self.next = self.next + (1,)

    def process_s(self):
        buffer = self.word.buffer
        position = self.position
        start_index = self.word.start_index
        end_index = self.word.end_index
        # special cases 'island', 'isle', 'carlisle', 'carlysle'
        if buffer[position - 1:position + 2] in ['ISL', 'YSL']:
            self.next = (None, 1)
        # special case 'sugar-'
        elif (position == start_index
              and buffer[start_index:start_index + 5] == 'SUGAR'):
            self.next = ('X', 'S', 1)
        elif buffer[position:position + 2] == 'SH':
            # germanic
            if buffer[position + 1:position + 5] in [
                "HEIM", "HOEK", "HOLM", "HOLZ"]:
                self.next = ('S', 2)
            else:
                self.next = ('X', 2)
        # italian & armenian
        elif (buffer[position:position + 3] in ["SIO", "SIA"]
              or buffer[position:position + 4] == 'SIAN'):
            if not self.word.is_slavo_germanic:
                self.next = ('S', 'X', 3)
            else:
                self.next = ('S', 3)
        # german & anglicisations, e.g. 'smith' match 'schmidt', 'snider'
        # match 'schneider' also, -sz- in slavic language altho in
        # hungarian it is pronounced 's'
        elif ((position == start_index
               and buffer[position + 1] in ["M", "N", "L", "W"])
              or buffer[position + 1] == 'Z'):
            self.next = ('S', 'X')
            if buffer[position + 1] == 'Z':
                self.next = self.next + (2,)
            else:
                self.next = self.next + (1,)
        elif buffer[position:position + 2] == 'SC':
            # Schlesinger's rule
            if buffer[position + 2] == 'H':
                # dutch origin, e.g. 'school', 'schooner'
                if buffer[position + 3:position + 5] in [
                    "OO", "ER", "EN", "UY", "ED", "EM"]:
                    # 'schermerhorn', 'schenker'
                    if buffer[position + 3:position + 5] in ['ER', 'EN']:
                        self.next = ('X', 'SK', 3)
                    else:
                        self.next = ('SK', 3)
                else:
                    if (position == start_index
                            and buffer[start_index + 3] not in VOWELS
                            and buffer[start_index + 3] != 'W'):
                        self.next = ('X', 'S', 3)
                    else:
                        self.next = ('X', 3)
            elif buffer[position + 2] in ['I', 'E', 'Y']:
                self.next = ('S', 3)
            else:
                self.next = ('SK', 3)
        # french e.g. 'resnais', 'artois'
        elif (position == end_index
              and buffer[position - 2:position] in ['AI', 'OI']):
            self.next = ('', 'S', 1)
        else:
            self.next = ('S',)
            if buffer[position + 1] in ['S', 'Z']:
                self.next = self.next + (2,)
            else:
                self.next = self.next + (1,)

    def process_t(self):
        buffer = self.word.buffer
        position = self.position
        start_index = self.word.start_index
        if buffer[position:position + 4] == 'TION':
            self.next = ('X', 3)
        elif buffer[position:position + 3] in ['TIA', 'TCH']:
            self.next = ('X', 3)
        elif (buffer[position:position + 2] == 'TH'
              or buffer[position:position + 3] == 'TTH'):
            # special case 'thomas', 'thames' or germanic
            if (buffer[position + 2:position + 4] in ['OM', 'AM']
                    or buffer[start_index:start_index + 4] in ['VON ', 'VAN ']
                    or buffer[start_index:start_index + 3] == 'SCH'):
                self.next = ('T', 2)
            else:
                self.next = ('0', 'T', 2)
        elif buffer[position + 1] in ['T', 'D']:
            self.next = ('T', 2)
        else:
            self.next = ('T', 1)

    def process_v(self):
        if self.word.buffer[self.position + 1] == 'V':
            self.next = ('F', 2)
        else:
            self.next = ('F', 1)

    def process_w(self):
        buffer = self.word.buffer
        position = self.position
        start_index = self.word.start_index
        # can also be in middle of word
        if buffer[position:position + 2] == 'WR':
            self.next = ('R', 2)
        elif (position == start_index
              and (buffer[position + 1] in VOWELS
                   or buffer[position:position + 2] == 'WH')):
            # Wasserman should match Vasserman
            if buffer[position + 1] in VOWELS:
                self.next = ('A', 'F', 1)
            else:
                self.next = ('A', 1)
        # Arnow should match Arnoff
        elif ((position == self.word.end_index
               and buffer[position - 1] in VOWELS)
              or buffer[position - 1:position + 4] in [
                  "EWSKI", "EWSKY", "OWSKI", "OWSKY"]
              or buffer[start_index:start_index + 3] == 'SCH'):
            self.next = ('', 'F', 1)
        # polish e.g. 'filipowicz'
        elif buffer[position:position + 4] in ["WICZ", "WITZ"]:
            self.next = ('TS', 'FX', 4)
        else:  # default is to skip it
            self.next = (None, 1)

    def process_x(self):
        buffer = self.word.buffer
        position = self.position
        # french e.g. breaux
        self.next = (None,)
        if not (
                position == self.word.end_index
                and (buffer[position - 3:position] in ["IAU", "EAU"]
                     or buffer[position - 2:position] in ['AU', 'OU'])):
            self.next = ('KS',)
        if buffer[position + 1] in ['C', 'X']:
            self.next = self.next + (2,)
        else:
            self.next = self.next + (1,)

    def process_z(self):
        # chinese pinyin e.g. 'zhao'
        if self.word.buffer[self.position + 1] == 'H':
            self.next = ('J',)
        elif (
                self.word.buffer[self.position + 1:self.position + 3] in [
            "ZO", "ZI", "ZA"]
                or (self.word.is_slavo_germanic
                    and self.position > self.word.start_index
                    and self.word.buffer[self.position - 1] != 'T')):
            self.next = ('S', 'TS')
        else:
            self.next = ('S',)
        if (self.word.buffer[self.position + 1] == 'Z'
                or self.word.buffer[self.position + 1] == 'H'):
            self.next = self.next + (2,)
        else:
            self.next = self.next + (1,)

    def parse(self, input_str):
        self.word = MetaphoneWord(input_str)
        self.position = self.word.start_index
        self.check_word_start()
        # loop through chars in word.buffer
        while self.position <= self.word.end_index:
            character = self.word.buffer[self.position]
            if character in VOWELS:
                self.process_vowels(character)
            elif character == ' ':
                self.position += 1
                continue
            elif character == 'B':
                self.process_b()
            elif character == 'C':
                self.process_c()
            elif character == 'D':
                self.process_d()
            elif character == 'F':
                self.process_f()
            elif character == 'G':
                self.process_g()
            elif character == 'H':
                self.process_h()
            elif character == 'J':
                self.process_j()
            elif character == 'K':
                self.process_k()
            elif character == 'L':
                self.process_l()
            elif character == 'M':
                self.process_m()
            elif character == 'N':
                self.process_n()
            elif character == 'P':
                self.process_p()
            elif character == 'Q':
                self.process_q()
            elif character == 'R':
                self.process_r()
            elif character == 'S':
                self.process_s()
            elif character == 'T':
                self.process_t()
            elif character == 'V':
                self.process_v()
            elif character == 'W':
                self.process_w()
            elif character == 'X':
                self.process_x()
            elif character == 'Z':
                self.process_z()

            if len(self.next) == 2:
                if self.next[0]:
                    self.primary_phone += self.next[0]
                    self.secondary_phone += self.next[0]
                    self.primary_phone_with_vowels += self.next[0]
                    self.secondary_phone_with_vowels += self.next[0]
                self.position += self.next[1]
            elif len(self.next) == 3:
                if self.next[0]:
                    self.primary_phone += self.next[0]
                    self.primary_phone_with_vowels += self.next[0]
                if self.next[1]:
                    self.secondary_phone += self.next[1]
                    self.secondary_phone_with_vowels += self.next[1]
                self.position += self.next[2]

            if self.next_vowel and self.next[0] not in VOWELS:
                self.primary_phone_with_vowels += self.next_vowel
                self.secondary_phone_with_vowels += self.next_vowel
            self.next_vowel = None

        if self.primary_phone == self.secondary_phone:
            self.secondary_phone = ""
        if self.primary_phone_with_vowels == self.secondary_phone_with_vowels:
            self.secondary_phone_with_vowels = ""

        return (self.primary_phone, self.secondary_phone), \
               (self.primary_phone_with_vowels, self.secondary_phone_with_vowels)


def vowel_metaphone(input_str):
    """
    Given an input string, return ((dm1, dm2), (vm1, vm2)).

    First 2-tuple is the double metaphone codes for the provided string.

    Second 2-tuple is the double metaphone codes with vowels inserted in their original place.

    The second element of these tuples (dm2 / vm2) will be an empty string
    if it is identical to the first element (dm1 / vm1).
    """
    return VowelMetaphone().parse(input_str)
