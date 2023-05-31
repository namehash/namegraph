import re
import argparse
import json
from collections import defaultdict

from vowel_metaphone import vowel_metaphone


def get_rhyme_suffix(s_vmet: str) -> str:
    vowel_positions = [match.start() for match in re.finditer(r'[AEIOUY]', s_vmet)]
    if len(vowel_positions) == 1 and vowel_positions[0] != len(s_vmet) - 1:
        return s_vmet[vowel_positions[0]:]  # ex.: czad [SAT | XAT] -> AT, smith [SMI0 | XMIT] -> I0
    elif (len(vowel_positions) == 1 and vowel_positions[0] != len(s_vmet) - 1) or \
            len(vowel_positions) > 1:
        return s_vmet[vowel_positions[-1] - 1:]  # ex.: crew [KRE] -> RE, affair [AFAIR] -> AIR, salmon [SALMON] -> MON
    else:
        return ''  # no rhymes for string without vowels


def create_suffix_dict(n_top: int):
    unigrams: list[str] = []
    with open('../../data/ngrams/unigram_freq.csv', encoding='utf-8') as f:
        for i, line in enumerate(f.readlines()):
            if i >= n_top:
                break
            unigrams.append(line.split(',')[0])

    suffix_dict: dict[str, list[str]] = defaultdict(list)
    for word in unigrams:
        word = word.upper()
        vmet_repr = vowel_metaphone(word)[1][0]
        if vmet_suffix := get_rhyme_suffix(vmet_repr):
            suffix_dict[vmet_suffix].append(word.lower())

    # unique, preserving order
    for suffix, rhymes in suffix_dict.items():
        seen = set()
        suffix_dict[suffix] = [r for r in rhymes if not (r in seen or seen.add(r))]

    with open('../../data/suffix_rhymes.json', 'w') as f:
        json.dump(suffix_dict, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Create json dictionary suffix -> rhymes (unigrams sharing suffix)."
    )
    parser.add_argument('--n_top_unigrams', help='how many top unigrams to use', default=75_000, type=int)
    args = parser.parse_args()
    create_suffix_dict(args.n_top_unigrams)

    # print(get_rhyme_suffix(vowel_metaphone('smith')[1][0]))
