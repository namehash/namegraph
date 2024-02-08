from argparse import ArgumentParser
import json
import csv


if __name__ == '__main__':
    parser = ArgumentParser(description="Takes the first column of a CSV file, which is the name of a related "
                                        "collection we have found, then maps it to the Elasticsearch IDs, and finally, "
                                        "writes to a TXT file to be later used in the archiving script.")
    parser.add_argument('--input', type=str, required=True, help='Path to the input CSV file')
    parser.add_argument('--mapping', type=str, required=True, help='Path to the mapping JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to the output TXT file')
    args = parser.parse_args()

    with open(args.mapping, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    with open(args.input, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        names = [row[0] for row in reader]

    with open(args.output, 'w', encoding='utf-8') as f:
        for name in names:
            if name in mapping:
                f.write(mapping[name] + '\n')
            else:
                print(f'Name "{name}" not found in mapping')
