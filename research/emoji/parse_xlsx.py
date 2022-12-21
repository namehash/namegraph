from argparse import ArgumentParser
from itertools import count
import json

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


def is_valid_color(color: str) -> bool:
    valid_colors = ['FFB6D7A8', 'FFD9EAD3']
    return color in valid_colors


def parser_xlsx(filepath: str):
    wb = load_workbook(filepath)
    ws = wb['Words']

    colors = set()
    name2emojis = dict()
    for row in count(2):
        name = ws[get_column_letter(2) + str(row)].value

        if not name:
            break

        emojis = []
        for column in count(4):
            coords = get_column_letter(column) + str(row)

            if not ws[coords].value:
                break

            if is_valid_color(ws[coords].fill.start_color.index):
                emojis.append(ws[coords].value)

        if emojis:
            name2emojis[name] = emojis

    return name2emojis


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('sheet', help='path to the xlsx file')
    parser.add_argument('output', help='path to the json output file')
    args = parser.parse_args()

    name2emojis = parser_xlsx(args.sheet)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(name2emojis, f, indent=2, ensure_ascii=False)
