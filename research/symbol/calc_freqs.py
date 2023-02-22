from argparse import ArgumentParser
from collections import defaultdict
import json
import csv


def load_all_symbols(filepath: str) -> set[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        name2symbols = json.load(f)

    all_symbols = set()
    for symbols in name2symbols.values():
        all_symbols.update(symbols)
    return all_symbols


def load_all_domains(filepath: str) -> list[str]:
    names = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        rows_iterator = iter(reader)
        next(rows_iterator)
        for row in rows_iterator:
            names.append(row[0])
    return names


def calculate_frequencies(symbols: list[str], domains: list[str]) -> dict[str, int]:
    frequencies: dict[str, int] = defaultdict(int)
    for domain in domains:
        for symbol in symbols:
            if symbol in domain:
                frequencies[symbol] += 1
    return frequencies


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('mapping', help='path to JSON mapping [name -> list of symbols]')
    parser.add_argument('domains', help='path to CSV files containing registered domains')
    parser.add_argument('output', help='path for the output JSON file')
    args = parser.parse_args()

    symbols = load_all_symbols(args.mapping)
    domains = load_all_domains(args.domains)
    frequencies = calculate_frequencies(list(symbols), domains)
    sorted_frequencies = {
        k: frequencies[k]
        for k in sorted(symbols, key=lambda x: frequencies[x], reverse=True)
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(sorted_frequencies, f, indent=2, ensure_ascii=False)
