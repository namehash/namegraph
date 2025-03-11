from argparse import ArgumentParser
import json


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('input', type=str, help='input JSON file with original affixes')
    parser.add_argument('emojify_output', type=str, help='output JSON file with emoji affixes')
    parser.add_argument('expand_output', type=str, help='output JSON file with ASCII affixes')
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        affixes = json.load(f)

    emojify_affixes = dict()
    expand_affixes = dict()

    emojify_count = 0
    expand_count = 0

    for key, d in affixes.items():
        emojify_affixes[key] = dict()
        expand_affixes[key] = dict()

        for affix, count in d.items():
            if not affix.isascii():
                emojify_affixes[key][affix] = count
                emojify_count += count
            else:
                expand_affixes[key][affix] = count
                expand_count += count

    with open(args.emojify_output, 'w') as f:
        json.dump(emojify_affixes, f, indent=2, ensure_ascii=False)

    with open(args.expand_output, 'w') as f:
        json.dump(expand_affixes, f, indent=2, ensure_ascii=False)

    print(f'Emojify affixes aggregated weight: {emojify_count}')
    print(f'Expand affixes aggregated weight: {expand_count}')
