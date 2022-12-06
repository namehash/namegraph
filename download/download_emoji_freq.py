from collections import defaultdict
from operator import itemgetter
from pathlib import Path
import tqdm
import json
import csv

import regex

import myunicode


PROJECT_ROOT_DIR = Path(__name__).parent.parent
_GRAPHEME_REGEX = regex.compile(r'\X')


def read_csv_names(path: str) -> list[str]:
    names = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        rows_iterator = iter(reader)
        next(rows_iterator)
        for row in rows_iterator:
            names.append(row[0])
    return names


def all_valid_emojis():
    all_possible_emojis = list(myunicode.emoji_iterator())
    to_remove = []
    for emoji in all_possible_emojis:
        try:
            normalized_emoji = myunicode.ens_normalize(emoji)
            if normalized_emoji != emoji:
                print('unnormalized emoji in iterator')
                print(emoji, normalized_emoji)
                print(myunicode.is_emoji(normalized_emoji))
                if myunicode.is_emoji(normalized_emoji):
                    all_possible_emojis.append(normalized_emoji)
        except ValueError:
            print('invalid emoji', emoji)
            to_remove.append(to_remove)

    valid_emojis = [emoji for emoji in all_possible_emojis if emoji not in to_remove]
    return valid_emojis


if __name__ == '__main__':
    names = read_csv_names(PROJECT_ROOT_DIR / 'data' / 'suggestable_domains.csv')
    emojis = set(all_valid_emojis())

    emoji_stats = defaultdict(int)
    for name in tqdm.tqdm(names):
        graphemes = set(_GRAPHEME_REGEX.findall(name))
        for grapheme in graphemes:
            if grapheme in emojis:
                emoji_stats[grapheme] += 1

    with open(PROJECT_ROOT_DIR / 'data' / 'ens-emoji-freq.json', 'w', encoding='utf-8') as f:
        json.dump({
            k: v
            for k, v in sorted(emoji_stats.items(), key=itemgetter(1), reverse=True)
        }, f, indent=2, ensure_ascii=False)
