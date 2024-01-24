from argparse import ArgumentParser
from typing import Optional
import json


def difference(
        mapping1: dict[str, list[str]],
        mapping2: dict[str, list[str]],
        order: bool = False,
        first: Optional[int] = None
) -> None:
    keys1 = set(mapping1.keys())
    keys2 = set(mapping2.keys())

    print(f'removed keys: {sorted(keys1 - keys2)}', end='\n\n')
    print(f'added keys: {sorted(keys2 - keys1)}', end='\n\n')

    for key in sorted(keys1 & keys2):
        emojis1 = mapping1[key]
        emojis2 = mapping2[key]

        if first:
            emojis1 = emojis1[:first]
            emojis2 = emojis2[:first]

        if order:
            if set(emojis1) == set(emojis2) and emojis1 != emojis2:
                print(key)
                print(f'- {emojis1}')
                print(f'- {emojis2}')
                print()

        else:
            if set(emojis1) != set(emojis2):
                added = [emoji for emoji in emojis2 if emoji not in emojis1]
                removed = [emoji for emoji in emojis1 if emoji not in emojis2]
                print(f'{key}')
                print(f'+{added}')
                print(f'-{removed}')
                print()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('filepath1', type=str, help='first mapping JSON filepath')
    parser.add_argument('filepath2', type=str, help='second mapping JSON filepath')
    parser.add_argument('--order', action='store_true', help='check order')
    parser.add_argument('--first', default=None, type=int, help='compare only first n suggestions')
    args = parser.parse_args()

    with open(args.filepath1, 'r', encoding='utf-8') as f:
        mapping1 = json.load(f)

    with open(args.filepath2, 'r', encoding='utf-8') as f:
        mapping2 = json.load(f)

    difference(mapping1, mapping2, order=args.order, first=args.first)
