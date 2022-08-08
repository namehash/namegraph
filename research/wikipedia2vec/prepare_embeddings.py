import re
import sys
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser(description="Process (lowercase, filter) wikipedia2vec embeddings.")
    parser.add_argument('input', help='input wikipedia2vec in text format (enwiki_20180420_100d.txt)')
    parser.add_argument('output', help='output wikipedia2vec in text format (enwiki_20180420_100d.txt.processed)')
    args = parser.parse_args()

    path = args.input
    output_path = args.output

    VALID_NAME = r'^[a-zA-Z0-9/_(),.#–-]+$'
    VALID_NAME_REGEXP = re.compile(VALID_NAME)

    # I guess file is sorted in popularity order, so we can add e.g. Nirvana from Nirvana_(band). however there is Nirvana later

    f = open(path)
    header = next(f)
    dim = int(header.split()[1])
    print(f'Dimension: {dim}', file=sys.stderr)

    f_out = open(output_path, 'w')
    f_out.write(header)
    all_tokens = set()
    for line in f:
        row = line.split(' ')
        assert len(row) == dim + 1
        token = row[0]

        if token.startswith('ENTITY/'):
            token = re.sub(r'^ENTITY/', '', token).lower()
            if not VALID_NAME_REGEXP.match(token):
                continue
            token = f'ENTITY/{token}'
        else:
            token = token.lower()
            if not VALID_NAME_REGEXP.match(token):
                continue

        row[0] = token

        if token not in all_tokens:
            all_tokens.add(token)

            f_out.write(' '.join(row))

    print(f'Tokens: {len(all_tokens)}', file=sys.stderr)
