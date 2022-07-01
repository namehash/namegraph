import collections
import unicodedata

import hydra
import regex
import unicodeblock.blocks

# print(ens.main.ENS.is_valid_name('🅜🅜🅜.eth'))
import wordninja
from omegaconf import DictConfig
from unidecode import unidecode

from inspector.confusables import Confusables
from emoji import emoji_count, unicode_codes


# http://www.unicode.org/Public/UCD/latest/ucd/Scripts.txt
# cat Scripts.txt | grep -v -P "^#" | cut -d ";" -f 2 | cut -d ' ' -f 2 | sort -u > script_names.txt

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


class Inspector:
    def __init__(self, config: DictConfig):
        self.config = config
        emojis = sorted(unicode_codes.EMOJI_DATA, key=len, reverse=True)
        emoji_pattern = u'(' + u'|'.join(regex.escape(u) for u in emojis) + u')'
        _EMOJI_REGEXP = regex.compile(emoji_pattern)
        EMOJI_REGEXP_AZ09 = regex.compile('^(' + emoji_pattern + '|[a-z0-9-])+$')

        self.regexp_patterns = {
            'latin-alpha': '^[a-z]+$',
            'numeric': '^[0-9]+$',
            'latin-alpha-numeric': '^[a-z0-9]+$',
            'simple': '^[a-z0-9-]+$',
            'emoji': emoji_pattern,
            'simple-emoji': '^(' + emoji_pattern + '|[a-z0-9-])+$',
            'literals': r'^\p{Ll}+$',  # include small caps http://www.unicode.org/reports/tr44/#GC_Values_Table
        }

        self.script_names = [line.strip() for line in open(config.inspector.script_names)]
        self.confusables = Confusables(config)

    def analyze_string(self, name):
        result = self.analyze_both(name)
        result['chars'] = len(name)
        # result['emoji_count'] = emoji_count(name)

        return result

    def analyze_character(self, name):
        result = self.analyze_both(name)

        # result['ascii'] = self._is_ascii(name)

        for pattern_name, pattern in self.regexp_patterns.items():
            result[pattern_name] = bool(regex.match(pattern, name, regex.UNICODE)) #TODO flags

        result['script_name'] = None
        for script_name in self.script_names:
            if regex.match(r'^\p{' + script_name + r'}+$', name):
                result['script_name'] = script_name

        result['zwj'] = '‍' == name
        result['zwnj'] = '‌' == name

        try:
            result['unicodedata.name'] = unicodedata.name(name)
        except ValueError:
            result['unicodedata.name'] = None
        result['unicodedata.category'] = unicodedata.category(name)
        result['unicodedata.bidirectional'] = unicodedata.bidirectional(name)
        result['unicodedata.combining'] = unicodedata.combining(name)
        result['unicodedata.mirrored'] = unicodedata.mirrored(name)
        result['unicodedata.decomposition'] = unicodedata.decomposition(name)
        result['unicodeblock'] = unicodeblock.blocks.of(name)

        is_confusable, canonical = self.confusables.analyze(name)
        result['confusables'] = is_confusable
        result['canonical'] = canonical

        # TODO codepoint
        result['codepoint'] = ord(name)
        result['codepoint_hex'] = hex(ord(name))

        result['link'] = f'https://unicode.link/codepoint/{ord(name):x}'

        return result

    def aggregate(self, characters_analysis):
        result = collections.defaultdict(list)
        for char_analysis in characters_analysis:
            for k, v in char_analysis.items():
                result[k].append(v)

        aggregated = {}
        for k, vs in result.items():
            if all([isinstance(x, bool) for x in vs]):
                aggregated[f'allTrue_{k}'] = all(vs)
                aggregated[f'anyTrue_{k}'] = any(vs)
            else:
                if len(set(vs)) == 1:
                    aggregated[f'all_{k}'] = vs[0]
                else:
                    aggregated[f'all_{k}'] = None
        return aggregated

    @staticmethod
    def _is_ascii(name):
        try:
            name.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def analyze_both(self, name):
        result = {}
        result['name'] = name
        result['bytes'] = len(name.encode('utf-8'))

        result['unidecode'] = unidecode(name, errors='ignore')
        result['NFKD_ascii'] = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
        result['NFD_ascii'] = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
        result['NFKD'] = unicodedata.normalize('NFKD', name)
        result['NFD'] = unicodedata.normalize('NFD', name)

        return result

    # TODO: valid according to ens

    # TODO token analysis

    # assume we got normalized and valid name
    def analyse_name(self, name: str):
        # result = {}
        name_analysis = self.analyze_string(name)

        chars_analysis = []
        for i, char in enumerate(name):
            char_analysis = self.analyze_character(char)
            char_analysis['index'] = i
            chars_analysis.append(char_analysis)
        name_analysis['characters_analysis'] = chars_analysis

        tokenized = wordninja.split(name)
        name_analysis['tokens'] = len(tokenized)
        tokens_analysis = []
        for i, token in enumerate(tokenized):  # TODO: wordninja is ok?
            token_analysis = self.analyze_string(token)
            token_analysis['index'] = i
            tokens_analysis.append(token_analysis)
        name_analysis['tokens_analysis'] = tokens_analysis

        aggregated = self.aggregate(chars_analysis)
        name_analysis['aggregated'] = aggregated
        return name_analysis


# for name in names:
#     print(name)
#     normalized = ens.main.ENS.nameprep(name)
#     print(normalized, normalized == name)
#     print(ens.main.ENS.is_valid_name(name))

@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def main(config: DictConfig):
    print('Unicode version', unicodedata.unidata_version)

    names = ['🅜🅜🅜', 'ന്‌മ', 'a‌b.eth', '1a〆.eth', 'аррӏе.eth', 'as', '.', 'ASD', 'Bloß.de', 'xn--0.pt', 'u¨.com',
             'a⒈com', 'a_a', 'a👍a', 'a‍a', 'łąść', 'ᴄeo', 'ǉeto', 'pаypаl', 'ѕсоре']

    inspector = Inspector(config)
    for name in names:
        print(name)
        print(inspector.analyse_name(name))


if __name__ == "__main__":
    main()

# TODO: And for each token, in each possible tokenization, to also include some metadata fields.
# TODO: documentation of fields
# TODO: ZWJ in emojis?
