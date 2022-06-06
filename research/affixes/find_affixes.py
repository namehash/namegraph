"""Finds prefixes/suffixes of registered domains, which were registered without prefixes/suffixes too."""
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
        affix = line.strip()
        if affix.endswith('.eth'):
            affix = affix[:-4]
        domains.append(affix)

print('Names:', len(domains), file=sys.stderr)

domains = [domain for domain in domains if re.match('^[a-z0-9-]+$', domain)]

print('Valid names:', len(domains), file=sys.stderr)
if not args.s:
    domains = [domain[::-1] for domain in domains]

import marisa_trie

trie = marisa_trie.Trie(domains)

affixes = collections.defaultdict(int)

for affix in domains:
    for longer_name in trie.keys(affix):
        if affix == longer_name: continue
        affix = longer_name[len(affix):]
        affixes[affix] += 1

for affix, count in sorted(affixes.items(), key=lambda x: x[1], reverse=True)[:1000]:
    if args.s:
        print(affix, count)
    else:
        print(affix[::-1], count)
