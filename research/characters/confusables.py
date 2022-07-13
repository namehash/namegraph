import collections
import json
import sys
import unicodedata
from typing import List, Dict, Callable

import regex
from tqdm import tqdm
from unidecode import unidecode


def hex_to_char(hex_string: str) -> str:
    """Convert hex string to character (e.g. '0061' to 'a')."""
    return chr(int(hex_string, 16))


def read_confusables_txt(path='confusables.txt') -> Dict[str, List[str]]:
    """Read confusables.txt"""
    rules = collections.defaultdict(list)
    for line in open(path):
        if line.startswith('#'):
            continue
        line = line[:-1] if line[-1] == '\n' else line
        row = line.split(' ;\t')
        if len(row) >= 2:
            a = ''.join([hex_to_char(hex_string) for hex_string in row[0].split(' ')])
            b = ''.join([hex_to_char(hex_string) for hex_string in row[1].split(' ')])
            rules[a].append(b)
    return rules


def uniq(l: List) -> List:
    """Return list with unique elements."""
    used = set()
    return [x for x in l if x not in used and (used.add(x) or True)]


def uniq_filter(l: List) -> List:
    """Return list with unique non-empty elements."""
    return [x for x in uniq(l) if x]


def normalizations() -> Dict[str, List[str]]:
    """Create confusable rules by normalizations."""
    upto = sys.maxunicode + 1
    rules = collections.defaultdict(list)
    for i in range(0, upto):
        char = chr(i)
        variants = uniq_filter(all_variants(char))
        if len(variants) > 1 or (len(variants) == 1 and variants[0] != char):
            rules[char].extend(variants)
    return rules


def all_variants(s: str) -> List[str]:
    """Return all normalizations."""
    nfkd_form = unicodedata.normalize('NFKD', s)
    nfd_form = unicodedata.normalize('NFD', s)
    nfc_form = unicodedata.normalize('NFC', s)
    nfkc_form = unicodedata.normalize('NFKC', s)
    result = [nfkd_form, nfd_form, nfc_form, nfkc_form]
    if s in result:
        result.remove(s)
    return result


def remove_accents(input_str):
    """Removes accents by stripping combining characters after decomposition."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def apply_all_chars(func: Callable) -> Dict[str, List[str]]:
    """Applies a transformation for every Unicode char."""
    upto = sys.maxunicode + 1
    rules = collections.defaultdict(list)
    for i in range(0, upto):
        char = chr(i)
        stripped = func(char)
        variants = uniq_filter([stripped] + all_variants(stripped))
        if len(variants) > 1 or (len(variants) == 1 and variants[0] != char):
            rules[char].extend(variants)
    return rules


def removed_accents() -> Dict[str, List[str]]:
    return apply_all_chars(remove_accents)


def unidecoded() -> Dict[str, List[str]]:
    """Create confusable rules using unidecode library."""
    upto = sys.maxunicode + 1
    rules = collections.defaultdict(list)
    for i in range(0, upto):
        char = chr(i)
        stripped = unidecode(char)
        if len(stripped) > 1: continue
        variants = uniq_filter([stripped] + all_variants(stripped))
        if len(variants) > 1 or (len(variants) == 1 and variants[0] != char):
            rules[char].extend(variants)
    return rules


def strip_accents(s: str, categories=('Mn',), n='NFD') -> str:
    """Removes accents by stripping characters within given categories."""
    return ''.join(c for c in unicodedata.normalize(n, s)
                   if unicodedata.category(c) not in categories)


def strip_accents_nfd() -> Dict[str, List[str]]:
    return apply_all_chars(lambda x: strip_accents(x, n='NFD', categories=['Mn']))


def strip_accents_nfkd() -> Dict[str, List[str]]:
    return apply_all_chars(
        lambda x: strip_accents(x, n='NFKD', categories=['Mn', 'Zs', 'Nd', 'Sm', 'Po', 'Lm', 'Lo', 'Mc', 'So']))


def reorder(l: List[str]) -> List[str]:
    """Reorder list of string so in the first place is a character [a-z0-9-]."""
    simple = None
    for el in l:
        if regex.match(r'^[a-z0-9-]$', el):
            simple = el
            break
    if simple is not None:
        l.remove(simple)
        return [simple] + l
    else:
        return l


def uniq_and_reorder(c: Dict[str, List[str]]):
    """Remove duplicates from values of confusable rules and reorder them."""
    for key, values in c.items():
        u = uniq(values)
        if key in u:
            u.remove(key)
        c[key] = reorder(u)


def forward_backward_transitive(rules: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Augments confusable rules. If the rules are: a->b; c->b then a->b,c; c->b,a."""
    reversed_c = collections.defaultdict(list)
    for key, values in tqdm(rules.items(), desc='Reversing'):
        for v in values:
            reversed_c[v].append(key)

    new_rules = collections.defaultdict(list)
    new_rules.update(rules)
    for key, values in tqdm(rules.items(), desc='Backward transitive'):
        for v in values:
            new_rules[key].extend(reversed_c[v])
    return new_rules


def symmetric(rules: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Augments confusable rules. If the rules are: a->b then b->a."""
    new_rules = collections.defaultdict(list)
    new_rules.update(rules)
    for key, values in tqdm(rules.items(), desc='Symmetric'):
        for v in list(values):
            new_rules[v].append(key)
    return new_rules


class Confusables():
    """Generate confusable rules."""

    def __init__(self):

        rule_generators = [read_confusables_txt, normalizations, removed_accents, unidecoded, strip_accents_nfd,
                           strip_accents_nfkd]

        # join rules
        self.rules: Dict[str, List[str]] = collections.defaultdict(list)
        for rule_generator in rule_generators:
            c_other = rule_generator()
            for key, values in c_other.items():
                self.rules[key].extend(values)
            print('added:', len(c_other), 'uniq:', len(self.rules))

        uniq_and_reorder(self.rules)
        # json.dump(rules, open('c.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)

        self.rules = forward_backward_transitive(self.rules)

        self.rules = symmetric(self.rules)

        uniq_and_reorder(self.rules)

    def save(self, path):
        json.dump(self.rules, open(path, 'w'), ensure_ascii=False, indent=2, sort_keys=True)


confusables = Confusables()
confusables.save('confusables.json')
