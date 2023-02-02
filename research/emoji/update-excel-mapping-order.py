from argparse import ArgumentParser
import json


def reorder_excel_mapping(
        excel_mapping: dict[str, dict[str, list[str]]],
        ordered_mapping: dict[str, list[str]]
) -> dict[str, dict[str, list[str]]]:

    new_excel_mapping = dict()
    for token, value in excel_mapping.items():

        if token not in ordered_mapping:
            new_excel_mapping[token] = value
            continue

        new_excel_mapping[token] = dict()
        if 'green' in value:
            filtered = value.get('yellow', []) + value.get('red', [])
            ordered = [emoji for emoji in ordered_mapping[token] if emoji not in filtered]
            new_excel_mapping[token]['green'] = ordered

        if 'yellow' in value:
            new_excel_mapping[token]['yellow'] = value['yellow']

        if 'red' in value:
            new_excel_mapping[token]['red'] = value['red']

    return new_excel_mapping


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('excel_mapping',
                        help='excel mapping, which greens order will be updated')
    parser.add_argument('mapping',
                        help='generated mapping, in which we assume the order is correct')
    parser.add_argument('--output', type=str, default=None,
                        help='output path, if not passed using the original path of excel mapping')
    args = parser.parse_args()

    with open(args.excel_mapping, 'r', encoding='utf-8') as f:
        excel_mapping = json.load(f)

    with open(args.mapping, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    ordered_excel_mapping = reorder_excel_mapping(excel_mapping, mapping)

    output = args.output if args.output is not None else args.excel_mapping
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(ordered_excel_mapping, f, indent=2, ensure_ascii=False)
