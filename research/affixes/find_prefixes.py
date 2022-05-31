"""Finds prefixes of registered domains, which were registered without prefixes too."""
import argparse
import collections
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument('path', help='path to text file with names')
parser.add_argument('-s', action='store_true', help='find suffixes instead of prefixes')
args = parser.parse_args()


path = args.path
domains = []
with open(path) as domains_file:
    for line in domains_file:
        name=line.strip()
        if name.endswith('.eth'):
            name=name[:-4]
        domains.append(name)

print('Names:', len(domains), file=sys.stderr)

domains = [domain for domain in domains if re.match('^[a-z0-9-]+$', domain)]

print('Valid names:', len(domains), file=sys.stderr)
if not args.s:
    domains = [domain[::-1] for domain in domains]

import marisa_trie

trie = marisa_trie.Trie(domains)

suffixes = collections.defaultdict(int)

for name in domains:
    for name2 in trie.keys(name):
        if name == name2: continue
        suffix = name2[len(name):]
        suffixes[suffix] += 1

for name, count in sorted(suffixes.items(), key=lambda x: x[1], reverse=True)[:1000]:
    if args.s:
        print(name, count)
    else:
        print(name[::-1], count)
