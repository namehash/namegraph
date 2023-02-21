import argparse
import collections
import csv
import json
import os
import random
import sys

import regex

from tqdm import tqdm

parser = argparse.ArgumentParser(description="Find affixees of registered person names")
parser.add_argument('path', help='path to text file with names')
parser.add_argument('-b', action='store_true', help='find affixes only at beginning or ending of names')
args = parser.parse_args()

path = args.path
male_first_names = open(os.path.dirname(os.path.realpath(__file__)) + '/english_male_names.txt').readlines()
male_first_names = [n.strip().lower() for n in male_first_names if len(n.strip()) >= 4]

female_first_names = open(os.path.dirname(os.path.realpath(__file__)) + '/english_female_names.txt').readlines()
female_first_names = [n.strip().lower() for n in female_first_names if len(n.strip()) >= 4]

first_names = male_first_names + female_first_names
first_names_regex = '(' + '|'.join(first_names) + ')'

if args.b:
    reg = regex.compile('^' + first_names_regex + '|' + first_names_regex + '$')
else:
    reg = regex.compile(first_names_regex)

domains = []
with open(path, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        affix = row[0]
        if affix.endswith('.eth'):
            affix = affix[:-4]
        domains.append(affix)

print('Names:', len(domains), file=sys.stderr)

domains = [domain for domain in domains if len(domain) <= 30]

print('Valid names:', len(domains), file=sys.stderr)

female_first_names = set(female_first_names)
male_first_names = set(male_first_names)
m_prefixes = collections.defaultdict(list)
m_suffixes = collections.defaultdict(list)
f_prefixes = collections.defaultdict(list)
f_suffixes = collections.defaultdict(list)

for domain in tqdm(domains):
    m = reg.search(domain)
    if not m: continue
    name = m.group(0)
    index = domain.index(name)

    if name in male_first_names:
        m_prefixes[domain[:index]].append(domain)
        m_suffixes[domain[index + len(name):]].append(domain)
    if name in female_first_names:
        f_prefixes[domain[:index]].append(domain)
        f_suffixes[domain[index + len(name):]].append(domain)

result = {
    'f_prefixes': [],
    'f_suffixes': [],
    'm_prefixes': [],
    'm_suffixes': [],
}

for key, d in [['f_prefixes', f_prefixes], ['f_suffixes', f_suffixes], ['m_prefixes', m_prefixes],
               ['m_suffixes', m_suffixes]]:
    for affix, count in sorted(d.items(), key=lambda x: len(x[1]), reverse=True)[:10000]:
        if count == 1: continue
        random.shuffle(count)
        result[key].append((affix, len(count), count[:5]))

json.dump(result, open('s.json', 'w'), indent=2, ensure_ascii=False)
