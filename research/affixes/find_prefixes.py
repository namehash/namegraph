"""Finds prefixes of registered domains, which were registered without prefixes too."""

import collections
import re
import sys

path = 'data/domains.sorted.csv'
domains = []
with open(path) as domains_file:
    for line in domains_file:
        domains.append(line.strip()[:-4])

print('Names:', len(domains), file=sys.stderr)

domains = [domain for domain in domains if re.match('^[a-z0-9-]+$', domain)]

print('Valid names:', len(domains), file=sys.stderr)
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
    print(name[::-1], count)
