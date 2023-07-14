from argparse import ArgumentParser
import json
import csv

import openpyxl


def generate_emojis(query: str, emoji_mapping: dict[str, list[str]], max_emojis: int = 10) -> list[str]:
    tokens = query.lower().split()
    present_tokens = len([token for token in tokens if token in emoji_mapping])
    if not present_tokens:
        return []

    max_emojis_per_token = max_emojis // present_tokens

    emojis = []
    for token in tokens:
        if token in emoji_mapping:
            for emoji in emoji_mapping[token][:max_emojis_per_token]:
                if emoji not in emojis:
                    emojis.append(emoji)
    return emojis


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('types_with_counts', type=str, help='types with counts, CSV format')
    parser.add_argument('emoji_mapping', type=str, help='emoji mapping, JSON format')
    parser.add_argument('output', type=str, help='output file, XLSX format')
    parser.add_argument('--first-n', type=int, default=50, help='number of types to generate emojis for')
    parser.add_argument('--max-emojis', type=int, default=20, help='maximum number of emojis to generate for each type')
    args = parser.parse_args()

    # reading types with counts
    types_with_counts = {}
    with open(args.types_with_counts, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            type_id = row[0]
            type_name = row[1]
            count = int(row[2])
            types_with_counts[type_id] = (type_name, count)

    all_counts = sum(count for _, count in types_with_counts.values())

    # reading emoji mapping
    with open(args.emoji_mapping, 'r', encoding='utf-8') as f:
        emoji_mapping = json.load(f)

    # writing the results to an XLSX file
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Types with counts'
    ws.append(['type_id', 'type_name', 'count', 'coverage', 'emojis'])

    coverage = 0
    for type_id, (type_name, count) in sorted(types_with_counts.items(),
                                              key=lambda x: x[1][1],
                                              reverse=True)[:args.first_n]:
        coverage += count
        emojis = generate_emojis(type_name, emoji_mapping, max_emojis=args.max_emojis)
        ws.append([type_id, type_name, count, coverage / all_counts] + emojis)

    wb.save(args.output)
