import collections
import unicodedata
from itertools import islice
from typing import Dict, Callable, List, Tuple, Any, Iterable

import hydra
import regex
import spacy
from spacy.tokens import Doc

from omegaconf import DictConfig

# http://www.unicode.org/Public/UCD/latest/ucd/Scripts.txt
# cat Scripts.txt | grep -v -P "^#" | cut -d ";" -f 2 | cut -d ' ' -f 2 | sort -u > script_names.txt
from generator.tokenization import AllTokenizer
from inspector.features import Features
from inspector.ngrams import Ngrams


def remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def uniq_gaps(tokenized: Iterable[str]) -> List[str]:
    result = []
    before_empty = False
    for token in tokenized:
        if token != '':
            result.append(token)
            before_empty = False
        else:
            if not before_empty:
                before_empty = True
                result.append('')
    return result


def count_words(tokenizeds: List[Dict]) -> int:
    count = [len(tokenized['tokens']) for tokenized in tokenizeds if '' not in tokenized['tokens']]
    if not count:
        return 0
    else:
        return min(count)


class Inspector:
    def __init__(self, config: DictConfig):
        self.config = config
        self.f = Features(config)
        self.ngrams = Ngrams(config)
        self.aggregate_config = {
            'any_emoji': ('is_emoji', 'any'),
            'any_invisible': ('is_invisible', 'any'),
            'all_unicodeblock': ('unicodeblock', 'all'),
            'any_confusable': ('confusable', 'any'),
        }

        self.combine_config = {
            'any_classes': ['any_emoji', 'any_invisible', 'any_confusable']
        }
        # TODO: MODE: filtering, ML

        # name of feature, function, if in filtering mode
        self.features_config: Dict[str, Dict[str, Tuple[Callable, bool]]] = {
            'string': {
                'name': (self.f.name, True),
                'length': (self.f.length, True),
                'emoji_count': (self.f.emoji_count, False),
                'bytes': (self.f.bytes, False),
                'all_classes': (self.f.classes, True),
                'all_script': (self.f.script_name, True),
                'all_letter': (self.f.is_letter, True),
                'all_number': (self.f.simple_number, True),
                'all_emoji': (self.f.is_emoji, True),
                'all_simple': (self.f.latin_alpha_numeric, True),
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
                'classes': (self.f.classes, False),
                'char_class': (self.f.char_class, True),

                'is_letter': (self.f.is_letter, True),
                'is_number': (self.f.simple_number, True),
                'is_hyphen': (self.f.is_hyphen, True),
                'is_emoji': (self.f.is_emoji, True),
                'is_simple': (self.f.latin_alpha_numeric, True),
                'is_invisible': (self.f.invisible, True),

                'simple_letter': (self.f.simple_letter, True),
                'simple_letter_emoji': (self.f.simple_letter_emoji, True),
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
                'confusable': (self.f.is_confusable, False),
                'confusables': (self.f.get_confusables, True),
                'canonical': (self.f.get_canonical, False),
                'ascii': (self.f.is_ascii, False),
                'codepoint_int': (self.f.codepoint_int, False),
                'codepoint_hex': (self.f.codepoint, False),
                'bytes': (self.f.bytes, False),
                'unidecode': (self.f.unidecode, True),
                'NFKD_ascii': (self.f.NFKD_ascii, False),
                'NFD_ascii': (self.f.NFD_ascii, False),
                'NFKD': (self.f.NFKD, False),
                'NFD': (self.f.NFD, False),
            },
            'token': {
                'token': (self.f.name, True),
                'length': (self.f.length, True),
                'all_classes': (self.f.token_classes, True),
                'all_script': (self.f.script_name, True),
                'all_letter': (self.f.is_letter, True),
                'all_number': (self.f.simple_number, True),
                'all_emoji': (self.f.is_emoji, True),
                'all_simple': (self.f.latin_alpha_numeric, True),
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
                'classes': (self.f.classes, False),
                'char_class': (self.f.char_class, True),
            },

        }
        # “token”:”laptop”,
        # “lemma”:”laptop”,
        # “parts - of - speech”:”noun, verb”,
        # “tense”:”???”,
        # “wiki - entities”:”a, b, c, d???”,
        # “categories”:”???”

        self.tokenizer = AllTokenizer(config)

        self.nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "parser", "ner"])  # ner is slow

    def analyze_string(self, name) -> Dict[str, Any]:
        result = {}

        for feature, (func, in_filtering) in self.features_config['string'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def analyze_token(self, name: str) -> Dict[str, Any]:
        result = {}

        for feature, (func, in_filtering) in self.features_config['token'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def analyze_character(self, name: str) -> Dict[str, Any]:
        result = {}
        for feature, (func, in_filtering) in self.features_config['char'].items():
            if in_filtering: result[feature] = func(name)

        return result

    def analyze_confusable(self, name: str) -> Dict[str, Any]:
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

    def combine_fields(self, analysis: Dict[str, Any], prefix_to_remove=''):
        for result_name, names in self.combine_config.items():
            result = []
            for name in names:
                if analysis[name]:
                    name = regex.sub(f'^{prefix_to_remove}', '', name)
                    result.append(name)
            analysis[result_name] = result

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

    def chars_analysis(self, name: str) -> List[Dict[str, Any]]:
        chars_analysis = []
        for i, char in enumerate(name):
            char_analysis = self.analyze_character(char)
            confusable_strings_analysis = []
            for confusable_string in char_analysis['confusables']:
                confusable_string_analysis = []
                for confusable_char in confusable_string:
                    confusable_char_analysis = self.analyze_confusable(confusable_char)
                    confusable_string_analysis.append(confusable_char_analysis)
                confusable_strings_analysis.append(confusable_string_analysis)
            char_analysis['confusables'] = confusable_strings_analysis
            chars_analysis.append(char_analysis)
        return chars_analysis

    def tokenize(self, name: str) -> List[Dict]:
        if len(name) > self.config.inspector.tokenization_length_threshold:
            return []

        tokenizeds = list(islice(self.tokenizer.tokenize(name), self.config.inspector.alltokenizer_limit))
        tokenizeds = [{'tokens': tokenized, 'probability': self.ngrams.sequence_probability(tokenized)} for tokenized in
                      tokenizeds]
        for tokenized in tokenizeds:
            tokenized['tokens'] = tuple(uniq_gaps(tokenized['tokens']))

        # sort so highest probability with the same tokenization is first
        tokenizeds = sorted(tokenizeds, key=lambda tokenized: tokenized['probability'], reverse=True)
        # remove duplicates after empty duplicates removal
        used = set()
        tokenizeds = [x for x in tokenizeds if x['tokens'] not in used and (used.add(x['tokens']) or True)]

        return tokenizeds

    def tokenizations_analysis(self, tokenizeds: List[Dict]) -> List[Dict[str, Any]]:
        for tokenized in tokenizeds:
            tokens_analysis = []
            for i, token in enumerate(tokenized['tokens']):
                token_analysis = self.analyze_token(token)
                token_analysis['probability'] = self.ngrams.word_probability(token)
                tokens_analysis.append(token_analysis)

            # spacy on tokenized form

            tokenized['tokens'] = tokens_analysis

        for tokenized in tokenizeds:  # TODO: limit spacy
            self.spacy(tokenized['tokens'])
        return tokenizeds

    # assume we got normalized and valid name
    def analyse_name(self, name: str):
        name_analysis = self.analyze_string(name)

        name_analysis['chars'] = self.chars_analysis(name)

        # tokenizeds = [wordninja.split(name)]
        tokenizeds = self.tokenize(name)

        # count min number of words for tokenization without gaps
        name_analysis['word_length'] = count_words(tokenizeds)

        name_analysis['tokenizations'] = self.tokenizations_analysis(tokenizeds)

        # sum probabilities
        name_analysis['probability'] = sum(
            [tokenization['probability'] for tokenization in name_analysis['tokenizations']])

        aggregated = self.aggregate(name_analysis['chars'])
        name_analysis.update(aggregated)

        self.combine_fields(name_analysis, prefix_to_remove='any_')

        return name_analysis

    def spacy(self, tokens_analysis):
        """Adds POS and lemmas to tokens."""
        # TODO: slow
        # use batching with nlp.pipe()
        mapping = {}
        tokens = []
        for i, token_analysis in enumerate(tokens_analysis):
            if token_analysis['token'] != '':
                mapping[len(tokens)] = i
                tokens.append(token_analysis['token'])

        doc = Doc(self.nlp.vocab, tokens)  # TODO: cache because after removing gaps there are duplicates
        for i, token in enumerate(self.nlp(doc)):
            token_analysis = tokens_analysis[mapping[i]]
            token_analysis['pos'] = token.pos_
            token_analysis['lemma'] = token.lemma_
            # token_analysis['dep'] = token.dep_


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
