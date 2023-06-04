import re
import argparse
import json
from collections import defaultdict

from vowel_metaphone import vowel_metaphone


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


def create_suffix_dict(n_top: int):
    unigrams: list[str] = []

    with open('stop_words.txt', 'r', encoding='utf-8') as f:
        stop_words = list(map(lambda x: x.strip(), f.readlines()))

    with open('../../data/ngrams/unigram_freq.csv', encoding='utf-8') as f:
        for i, line in enumerate(f.readlines()):
            if i >= n_top:
                break
            w = line.split(',')[0]
            if w not in stop_words:
                unigrams.append(w)

    suffix_dict: dict[str, list[str]] = defaultdict(list)
    for word in unigrams:
        word = word.upper()
        vmet_repr = vowel_metaphone(word)[1][0]
        if len(vmet_repr) >= 3:
            if vmet_suffix := get_rhyme_suffix(vmet_repr):
                suffix_dict[vmet_suffix].append(word.lower())

    # unique, preserving order
    for suffix, rhymes in suffix_dict.items():
        seen = set()
        suffix_dict[suffix] = [r for r in rhymes if not (r in seen or seen.add(r))]

    with open('../../data/suffix2rhymes.json', 'w') as f:
        json.dump(suffix_dict, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Create json dictionary suffix -> rhymes (unigrams sharing suffix)."
    )
    parser.add_argument('--n_top_unigrams', help='how many top unigrams to use', default=100_000, type=int)
    args = parser.parse_args()
    create_suffix_dict(args.n_top_unigrams)

    # print(get_rhyme_suffix(vowel_metaphone('smith')[1][0]))
