import collections
import unicodedata
from typing import Dict, Callable, List, Tuple

import hydra

# print(ens.main.ENS.is_valid_name('🅜🅜🅜.eth'))
import wordninja
from omegaconf import DictConfig

# http://www.unicode.org/Public/UCD/latest/ucd/Scripts.txt
# cat Scripts.txt | grep -v -P "^#" | cut -d ";" -f 2 | cut -d ' ' -f 2 | sort -u > script_names.txt
from inspector.features import Features


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


class Inspector:
    def __init__(self, config: DictConfig):
        self.config = config
        self.f = Features(config)
        self.features_config: Dict[str, Dict[str, Tuple[Callable, bool]]] = {
            'string': {
                'length': (self.f.length, True),
                'emoji_count': (self.f.emoji_count, False),
                'bytes': (self.f.bytes, False),
            },
            'char': {
                'latin-alpha': (self.f.latin_alpha, True),
                'numeric': (self.f.numeric, True),
                'latin-alpha-numeric': (self.f.latin_alpha_numeric, True),
                'is_basic': (self.f.simple, True),
                'is_emoji': (self.f.is_emoji, True),
                'simple-emoji': (self.f.simple_emoji, True),
                'is_letter': (self.f.is_letter, True),
                'zwj': (self.f.zwj, True),
                'zwnj': (self.f.zwnj, True),
                'unicodedata.name': (self.f.unicodedata_name, True),
                'unicodedata.category': (self.f.unicodedata_category, True),
                'unicodedata.bidirectional': (self.f.unicodedata_bidirectional, True),
                'unicodedata.combining': (self.f.unicodedata_combining, True),
                'unicodedata.mirrored': (self.f.unicodedata_mirrored, True),
                'unicodedata.decomposition': (self.f.unicodedata_decomposition, True),
                'unicodeblock': (self.f.unicodeblock, True),
                'confusable': (self.f.is_confusable, True),
                'confusable_with': (self.f.get_confusables, True),
                'canonical': (self.f.get_canonical, True),
                'ascii': (self.f.is_ascii, False),
                'codepoint': (self.f.codepoint, True),
                'codepoint_int': (self.f.codepoint_int, False),
                'codepoint_hex': (self.f.codepoint_hex, False),
                'link': (self.f.link, True),
                'name': (self.f.name, True),
                'bytes': (self.f.bytes, False),
                'unidecode': (self.f.unidecode, True),
                'NFKD_ascii': (self.f.NFKD_ascii, True),
                'NFD_ascii': (self.f.NFD_ascii, True),
                'NFKD': (self.f.NFKD, True),
                'NFD': (self.f.NFD, True),
                'is_invisible': (self.f.invisible, True),
                'script_name': (self.f.script_name, True),
                'is_hyphen': (self.f.is_hyphen, True),
                'is_number': (self.f.is_number, True),
                'class': (self.f.classes, True),
            },
            'token': {},
            'confusables': {
                'char': (self.f.name, True),
                'script_name': (self.f.script_name, True),
                'unicodedata.name': (self.f.unicodedata_name, True),
                'codepoint': (self.f.codepoint, True),
                'link': (self.f.link, True),
                'class': (self.f.classes, True),
            },

        }
        # TODO: MODE: filtering, ML

        # name of feature, function, if in filtering mode

    def analyze_string(self, name):
        result = {}

        for feature, (func, in_filtering) in self.features_config['string'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def analyze_character(self, name):
        result = {}
        for feature, (func, in_filtering) in self.features_config['char'].items():
            if in_filtering: result[feature] = func(name)

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

    # TODO: valid according to ens

    # TODO token analysis

    # assume we got normalized and valid name
    def analyse_name(self, name: str):
        # result = {}
        name_analysis = self.analyze_string(name)

        chars_analysis = []
        for i, char in enumerate(name):
            char_analysis = self.analyze_character(char)
            # char_analysis['index'] = i
            chars_analysis.append(char_analysis)
        name_analysis['chars'] = chars_analysis

        tokenized = wordninja.split(name)
        name_analysis['tokens'] = len(tokenized)
        tokens_analysis = []
        for i, token in enumerate(tokenized):  # TODO: wordninja is ok?
            token_analysis = self.analyze_string(token)
            token_analysis['index'] = i
            tokens_analysis.append(token_analysis)
        name_analysis['tokens'] = tokens_analysis

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
