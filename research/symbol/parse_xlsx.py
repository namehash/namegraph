from argparse import ArgumentParser
from collections import defaultdict
from itertools import count
import json

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


def parser_xlsx(filepath: str):
    wb = load_workbook(filepath)

    symbol2names = dict()
    for worksheet_name in ['other', 'math', 'currency']:
        ws = wb[worksheet_name]

        for row in count(1):
            symbol = ws[get_column_letter(2) + str(row)].value

            if not symbol:
                break

            names = []
            for column in count(4):
                coords = get_column_letter(column) + str(row)

                if not ws[coords].value:
                    break

                if ws[coords].font.bold:
                    names.append(ws[coords].value)

            if names:
                symbol2names[symbol] = names

    return symbol2names


def invert_mapping(symbol2names: dict[str, list[str]]) -> dict[str, list[str]]:
    name2symbols = defaultdict(list)
    for symbol, names in symbol2names.items():
        for name in names:
            name2symbols[name].append(symbol)

    return dict(name2symbols)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('sheet', help='path to the xlsx file')
    parser.add_argument('output', help='path to the json output file')
    args = parser.parse_args()

    symbol2names = parser_xlsx(args.sheet)
    name2symbols = invert_mapping(symbol2names)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(name2symbols, f, indent=2, ensure_ascii=False)
