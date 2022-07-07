import collections
import unicodedata
from typing import Dict, Callable, List, Tuple

import hydra
import spacy
from spacy.tokens import Doc

from omegaconf import DictConfig

# http://www.unicode.org/Public/UCD/latest/ucd/Scripts.txt
# cat Scripts.txt | grep -v -P "^#" | cut -d ";" -f 2 | cut -d ' ' -f 2 | sort -u > script_names.txt
from generator.tokenization import AllTokenizer
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
        self.aggregate_config = {
            'any_emoji': ('is_emoji', 'any'),
            'any_invisible': ('is_invisible', 'any'),
            'all_unicodeblock': ('unicodeblock', 'all'),
            'any_confusable': ('confusable', 'any'),
        }
        self.features_config: Dict[str, Dict[str, Tuple[Callable, bool]]] = {
            'string': {
                'name': (self.f.name, True),
                'length': (self.f.length, True),
                'emoji_count': (self.f.emoji_count, False),
                'bytes': (self.f.bytes, False),
                'all_classes': (self.f.classes, True),
                'all_script': (self.f.script_name, True),
                'all_letter': (self.f.is_letter, True),
                'all_number': (self.f.is_number, True),
                'all_emoji': (self.f.is_emoji, True),
                'all_basic': (self.f.latin_alpha_numeric, True),
                'in_dictionary': (self.f.in_dictionary, True),
                'ens_is_valid_name': (self.f.ens_is_valid_name, True),
                'ens_nameprep': (self.f.ens_nameprep, True),
                'uts46_remap': (self.f.uts46_remap, True),
                'idna_encode': (self.f.idna_encode, True),
            },
            'char': {
                'char': (self.f.name, True),
                'script': (self.f.script_name, True),
                'name': (self.f.unicodedata_name, True),
                'codepoint': (self.f.codepoint_hex, True),
                'link': (self.f.link, True),
                'classes': (self.f.classes, True),

                'is_letter': (self.f.is_letter, True),
                'is_number': (self.f.is_number, True),
                'is_hyphen': (self.f.is_hyphen, True),
                'is_emoji': (self.f.is_emoji, True),
                'is_basic': (self.f.latin_alpha_numeric, True),
                'is_invisible': (self.f.invisible, True),

                'latin-alpha': (self.f.latin_alpha, True),
                'numeric': (self.f.numeric, True),
                'latin-alpha-numeric': (self.f.latin_alpha_numeric, True),
                'simple-emoji': (self.f.simple_emoji, True),
                'zwj': (self.f.zwj, True),
                'zwnj': (self.f.zwnj, True),
                'unicodedata_category': (self.f.unicodedata_category, True),
                'unicodedata_bidirectional': (self.f.unicodedata_bidirectional, True),
                'unicodedata_combining': (self.f.unicodedata_combining, True),
                'unicodedata_mirrored': (self.f.unicodedata_mirrored, True),
                'unicodedata_decomposition': (self.f.unicodedata_decomposition, True),
                'unicodeblock': (self.f.unicodeblock, True),
                'confusable': (self.f.is_confusable, True),
                'confusable_with': (self.f.get_confusables, True),
                'canonical': (self.f.get_canonical, True),
                'ascii': (self.f.is_ascii, False),
                'codepoint_int': (self.f.codepoint_int, False),
                'codepoint_hex': (self.f.codepoint, False),
                'bytes': (self.f.bytes, False),
                'unidecode': (self.f.unidecode, True),
                'NFKD_ascii': (self.f.NFKD_ascii, True),
                'NFD_ascii': (self.f.NFD_ascii, True),
                'NFKD': (self.f.NFKD, True),
                'NFD': (self.f.NFD, True),
            },
            'token': {
                'token': (self.f.name, True),
                'length': (self.f.length, True),
                'all_classes': (self.f.classes, True),
                'all_script': (self.f.script_name, True),
                'all_letter': (self.f.is_letter, True),
                'all_number': (self.f.is_number, True),
                'all_emoji': (self.f.is_emoji, True),
                'all_basic': (self.f.latin_alpha_numeric, True),
                'in_dictionary': (self.f.in_dictionary, True),
                # 'lemma': (self.f.lemma, True),
                # 'pos': (self.f.pos, True),
                # 'tense': (self.f.name, True),
                # 'wiki-entities': (self.f.name, True),
                # 'categories': (self.f.name, True),
            },
            'confusable': {
                'char': (self.f.name, True),
                'script': (self.f.script_name, True),
                'name': (self.f.unicodedata_name, True),
                'codepoint': (self.f.codepoint_hex, True),
                'link': (self.f.link, True),
                'classes': (self.f.classes, True),
            },

        }
        # “token”:”laptop”,
        # “lemma”:”laptop”,
        # “parts - of - speech”:”noun, verb”,
        # “tense”:”???”,
        # “wiki - entities”:”a, b, c, d???”,
        # “categories”:”???”

        # TODO: MODE: filtering, ML

        # name of feature, function, if in filtering mode
        self.tokenizer = AllTokenizer(config)

        self.nlp = spacy.load("en_core_web_sm")

    def analyze_string(self, name):
        result = {}

        for feature, (func, in_filtering) in self.features_config['string'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def analyze_token(self, name):
        result = {}

        for feature, (func, in_filtering) in self.features_config['token'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def analyze_character(self, name):
        result = {}
        for feature, (func, in_filtering) in self.features_config['char'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def analyze_confusable(self, name):
        result = {}
        for feature, (func, in_filtering) in self.features_config['confusable'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def agg(self, vs, mode):
        if all([isinstance(x, bool) for x in vs]):
            if mode == 'all':
                return all(vs)
            elif mode == 'any':
                return any(vs)
        else:
            try:
                if len(set(vs)) == 1:
                    return vs[0]
                else:
                    return None
            except TypeError:
                pass
        return None

    def aggregate(self, characters_analysis):

        result = collections.defaultdict(list)
        for char_analysis in characters_analysis:
            for k, v in char_analysis.items():
                result[k].append(v)

        aggregated = {}
        for name, (feature, mode) in self.aggregate_config.items():
            aggregated[name] = self.agg(result[feature], mode)

        # for k, vs in result.items():
        #     if all([isinstance(x, bool) for x in vs]):
        #         aggregated[f'allTrue_{k}'] = all(vs)
        #         aggregated[f'anyTrue_{k}'] = any(vs)
        #     else:
        #         try:
        #             if len(set(vs)) == 1:
        #                 aggregated[f'all_{k}'] = vs[0]
        #             else:
        #                 aggregated[f'all_{k}'] = None
        #         except TypeError:
        #             pass
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
            confusable_strings_analysis = []
            for confusable_string in char_analysis['confusable_with']:
                confusable_string_analysis = []
                for confusable_char in confusable_string:
                    confusable_char_analysis = self.analyze_confusable(confusable_char)
                    confusable_string_analysis.append(confusable_char_analysis)
                confusable_strings_analysis.append(confusable_string_analysis)
            char_analysis['confusable_with'] = confusable_strings_analysis
            chars_analysis.append(char_analysis)
        name_analysis['chars'] = chars_analysis

        # tokenizeds = [wordninja.split(name)]
        tokenizeds = self.tokenizer.tokenize(name)
        # name_analysis['tokens'] = len(tokenized)
        name_analysis['tokens'] = []
        for tokenized in tokenizeds:
            tokens_analysis = []
            for i, token in enumerate(tokenized):
                token_analysis = self.analyze_token(token)
                # token_analysis['index'] = i
                tokens_analysis.append(token_analysis)

            # TODO spacy on tokenized form
            self.spacy(tokens_analysis)

            name_analysis['tokens'].append(tokens_analysis)

        aggregated = self.aggregate(chars_analysis)
        name_analysis['aggregated'] = aggregated
        return name_analysis

    def spacy(self, tokens_analysis):
        tokens = [token_analysis['token'] for token_analysis in tokens_analysis]
        # print(tokens)

        doc = Doc(self.nlp.vocab, tokens)
        for token, token_analysis in zip(self.nlp(doc), tokens_analysis):
            # print(token.text, token.pos_, token.dep_, token.lemma_)
            token_analysis['pos'] = token.pos_
            token_analysis['lemma'] = token.lemma_
            token_analysis['dep'] = token.dep_


# for name in names:
#     print(name)
#     normalized = ens.main.ENS.nameprep(name)
#     print(normalized, normalized == name)
#     print(ens.main.ENS.is_valid_name(name))

@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def main(config: DictConfig):
    print('Unicode version', unicodedata.unidata_version)

    names = ['🅜🅜🅜', 'ന്‌മ', 'a‌b.eth', '1a〆.eth', 'аррӏе.eth', 'as', '.', 'ASD', 'Bloß.de', 'xn--0.pt', 'u¨.com',
             'a⒈com', 'a_a', 'a👍a', 'a‍a', 'łąść', 'ᴄeo', 'ǉeto', 'pаypаl', 'ѕсоре', 'laptop']

    inspector = Inspector(config)
    for name in names:
        print(name)
        print(inspector.analyse_name(name))


if __name__ == "__main__":
    main()

# TODO: And for each token, in each possible tokenization, to also include some metadata fields.
# TODO: documentation of fields
# TODO: ZWJ in emojis?
# TODO: add version of name inspector
