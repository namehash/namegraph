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
            'all_unicodeblock': ('unicodeblock', 'all'),
            'all_class': ('char_class', 'all'),
            'any_classes': ('char_class', 'any'),
            'all_script': ('script', 'all'),
            'any_scripts': ('script', 'any'),
            'any_confusable': ('confusable', 'any'),

            # 'any_simple_letter': ('simple_letter', 'any'),
            # 'any_simple_number': ('simple_number', 'any'),
            # 'any_any_letter': ('any_letter', 'any'),
            # 'any_any_number': ('any_number', 'any'),
            # 'any_hyphen': ('hyphen', 'any'),
            # 'any_emoji': ('emoji', 'any'),
            # 'any_invisible': ('invisible', 'any'),
            # 'any_special': ('special', 'any'),
        }

        self.combine_config = {
            # 'any_classes': [
            # 'any_simple_letter',
            # 'any_simple_number',
            # 'any_any_letter',
            # 'any_any_number',
            # 'any_hyphen',
            # 'any_emoji',
            # 'any_invisible',
            # 'any_special'
            # ]
        }
        # TODO: MODE: filtering, ML

        # name of feature, function, if in filtering mode
        self.features_config: Dict[str, Dict[str, Tuple[Callable, bool]]] = {
            'string': {
                'name': (self.f.name, True),
                'length': (self.f.length, True),
                # 'emoji_count': (self.f.emoji_count, False),
                # 'bytes': (self.f.bytes, False),
                # 'all_classes': (self.f.classes, True),
                # 'all_script': (self.f.script_name, True),
                'all_letter': (self.f.is_letter, True),
                # 'all_number': (self.f.simple_number, True),
                # 'all_emoji': (self.f.is_emoji, True),
                'all_simple': (self.f.latin_alpha_numeric, True),
                'in_dictionary': (self.f.in_dictionary, True),
                'ens_is_valid_name': (self.f.ens_is_valid_name, True),
                'ens_nameprep': (self.f.ens_nameprep, True),
                # 'uts46_remap': (self.f.uts46_remap, True),
                'idna_encode': (self.f.idna_encode, True),
            },
            'char': {
                'char': (self.f.name, True),
                'script': (self.f.script_name, True),
                'name': (self.f.unicodedata_name, True),
                'codepoint': (self.f.codepoint_hex, True),
                'link': (self.f.link, True),
                # 'classes': (self.f.classes, False),
                'char_class': (self.f.char_class, True),

                # 'is_letter': (self.f.is_letter, True),
                # 'is_number': (self.f.simple_number, True),
                # 'is_hyphen': (self.f.is_hyphen, True),
                # 'is_emoji': (self.f.is_emoji, True),
                # 'is_simple': (self.f.latin_alpha_numeric, True),
                # 'is_invisible': (self.f.invisible, True),

                # 'simple_letter': (self.f.simple_letter, True),
                # 'simple_letter_emoji': (self.f.simple_letter_emoji, True),
                # 'numeric': (self.f.numeric, True),
                # 'latin-alpha-numeric': (self.f.latin_alpha_numeric, True),
                # 'simple-emoji': (self.f.simple_emoji, True),
                # 'zwj': (self.f.zwj, True),
                # 'zwnj': (self.f.zwnj, True),
                'unicodedata_category': (self.f.unicodedata_category, True),
                # 'unicodedata_bidirectional': (self.f.unicodedata_bidirectional, True),
                # 'unicodedata_combining': (self.f.unicodedata_combining, True),
                # 'unicodedata_mirrored': (self.f.unicodedata_mirrored, True),
                # 'unicodedata_decomposition': (self.f.unicodedata_decomposition, True),
                'unicodeblock': (self.f.unicodeblock, True),
                # 'confusable': (self.f.is_confusable, False),
                'confusables': (self.f.get_confusables, True),
                # 'canonical': (self.f.get_canonical, False),
                # 'ascii': (self.f.is_ascii, False),
                # 'codepoint_int': (self.f.codepoint_int, False),
                # 'codepoint_hex': (self.f.codepoint, False),
                # 'bytes': (self.f.bytes, False),
                # 'unidecode': (self.f.unidecode, True),
                # 'NFKD_ascii': (self.f.NFKD_ascii, False),
                # 'NFD_ascii': (self.f.NFD_ascii, False),
                # 'NFKD': (self.f.NFKD, False),
                # 'NFD': (self.f.NFD, False),
            },
            'token': {
                'token': (self.f.name, True),
                'length': (self.f.length, True),
                # 'all_classes': (self.f.token_classes, True),
                # 'all_script': (self.f.script_name, True),
                # 'all_letter': (self.f.is_letter, True),
                # 'all_number': (self.f.simple_number, True),
                # 'all_emoji': (self.f.is_emoji, True),
                # 'all_simple': (self.f.latin_alpha_numeric, True),
                # 'in_dictionary': (self.f.in_dictionary, True),
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

        self.nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "parser"])  # ner is slow

        self.scorer = Scorer(config)

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
            if mode == 'all':
                try:
                    if len(set(vs)) == 1:
                        return vs[0]
                    else:
                        return None
                except TypeError:
                    pass
            elif mode == 'any':
                return list(set(vs))
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

    def chars_analysis(self, name: str, limit_confusables: bool = False) -> List[Dict[str, Any]]:
        chars_analysis = []
        for i, char in enumerate(name):
            char_analysis = self.analyze_character(char)

            if limit_confusables:
                char_analysis['confusables'] = char_analysis['confusables'][:1]

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

    def tokenizations_analysis(self, tokenizeds: List[Dict], entities=False) -> List[Dict[str, Any]]:
        for tokenized in tokenizeds:
            tokens_analysis = []
            for i, token in enumerate(tokenized['tokens']):
                token_analysis = self.analyze_token(token)
                token_analysis['probability'] = self.ngrams.word_probability(token)
                tokens_analysis.append(token_analysis)

            # spacy on tokenized form

            tokenized['tokens'] = tokens_analysis

        for tokenized in tokenizeds:  # TODO: limit spacy
            self.spacy(tokenized, entities)
        return tokenizeds

    # assume we got normalized and valid name
    def analyse_name(self, name: str, tokenization: bool = True, entities: bool = False, limit_confusables: bool = False,
                     disable_chars_output: bool = False, disable_char_analysis: bool = False):
        name_analysis = self.analyze_string(name)

        if disable_char_analysis:
            name_analysis['chars'] = None
        else:
            name_analysis['chars'] = self.chars_analysis(name, limit_confusables=limit_confusables)

        # tokenizeds = [wordninja.split(name)]
        if tokenization and len(name) <= self.config.inspector.tokenization_length_threshold:
            tokenizeds = self.tokenize(name)

            # count min number of words for tokenization without gaps
            name_analysis['word_length'] = count_words(tokenizeds)

            name_analysis['tokenizations'] = self.tokenizations_analysis(tokenizeds, entities)

            # sum probabilities
            name_analysis['probability'] = sum(
                [tokenization['probability'] for tokenization in name_analysis['tokenizations']])

        if not disable_char_analysis:
            aggregated = self.aggregate(name_analysis['chars'])
            name_analysis.update(aggregated)

            self.combine_fields(name_analysis, prefix_to_remove='any_')

            if tokenization:
                name_analysis['score'] = self.score_name(name_analysis)

        if disable_chars_output:
            name_analysis['chars'] = None

        return name_analysis

    def spacy(self, tokenized: Dict[str, Any], entities: bool = False):
        """Adds POS and lemmas to tokens."""
        # TODO: slow
        # use batching with nlp.pipe()
        tokens_analysis = tokenized['tokens']
        mapping = {}
        tokens = []
        for i, token_analysis in enumerate(tokens_analysis):
            if token_analysis['token'] != '':
                mapping[len(tokens)] = i
                tokens.append(token_analysis['token'])

        doc = Doc(self.nlp.vocab, tokens)  # TODO: cache because after removing gaps there are duplicates
        next(self.nlp.pipe([doc], disable=[] if entities else ["ner"]))
        if entities:
            tokenized['entities'] = [(ent.text, ent.label_) for ent in doc.ents]
        for i, token in enumerate(doc):
            token_analysis = tokens_analysis[mapping[i]]
            token_analysis['pos'] = token.pos_
            token_analysis['lemma'] = token.lemma_
            # token_analysis['dep'] = token.dep_

    def score_name(self, name_analysis):
        return self.scorer.score(name_analysis)


class Scorer:
    def __init__(self, config):
        # self.config = config
        self.name_length_limit = config.app.name_length_limit

    def score(self, name_analysis) -> float:
        # TODO return 0 if namehash

        if self.name_contains_invisible(name_analysis):
            result = 1
        elif self.name_too_long(name_analysis):
            result = 2
        elif self.name_contains_confusable(name_analysis):
            result = 3
        elif self.name_contains_special(name_analysis):
            result = 4
        elif self.name_contains_number(name_analysis):
            result = 5
        elif self.name_contains_letters(name_analysis):
            result = 6
        elif self.name_contains_emoji(name_analysis):
            result = 7
        elif self.name_contains_hyphen(name_analysis):
            result = 8
        elif self.name_contains_simple_number(name_analysis):
            result = 9
        elif self.word_count(name_analysis) is None:
            result = 10
        elif self.word_count(name_analysis) == 0:
            result = 11
        elif self.word_count(name_analysis) >= 4:
            result = 12
        elif self.word_count(name_analysis) == 3:
            result = 13
        elif self.word_count(name_analysis) == 2:
            result = 14
        elif self.word_count(name_analysis) == 1:
            result = 15
        else:
            raise ValueError('error in name scoring algorithm')

        result += self.short_name_bonus(name_analysis)
        return result / 16

    def name_contains_invisible(self, name_analysis):
        return 'invisible' in name_analysis['any_classes']

    def name_too_long(self, name_analysis):
        return name_analysis['length'] > self.name_length_limit

    def name_contains_confusable(self, name_analysis):
        return any([char['confusables'] for char in name_analysis['chars']])

    def name_contains_special(self, name_analysis):
        return 'special' in name_analysis['any_classes']

    def name_contains_number(self, name_analysis):
        return 'any_number' in name_analysis['any_classes']

    def name_contains_letters(self, name_analysis):
        return 'any_letter' in name_analysis['any_classes']

    def name_contains_emoji(self, name_analysis):
        return 'emoji' in name_analysis['any_classes']

    def name_contains_hyphen(self, name_analysis):
        return 'hyphen' in name_analysis['any_classes']

    def name_contains_simple_number(self, name_analysis):
        return 'simple_number' in name_analysis['any_classes']

    def word_count(self, name_analysis):
        return name_analysis['word_length']

    def short_name_bonus(self, name_analysis):
        return 1 - min(name_analysis['length'], self.name_length_limit) / (self.name_length_limit + 1)


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
