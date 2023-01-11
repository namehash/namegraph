import collections
import json
import math

from tqdm import tqdm
from unidecode import unidecode, UnidecodeError

firstnames = json.load(open('firstnames_10kn.json'))
lastnames = json.load(open('lastnames_10kn.json'))


def agg(stats, name, name_stats):
    for country, gender_counts in name_stats.items():
        for gender, count in gender_counts.items():
            stats[name][country][gender] += count


def lower_simplify(raw_stats):
    firstname_stats = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))

    for name, name_stats in tqdm(list(raw_stats.items())):
        lowered_name = name.lower()
        agg(firstname_stats, lowered_name, name_stats)

        try:
            simplified_name = unidecode(lowered_name, errors='strict')
            if simplified_name != lowered_name:
                agg(firstname_stats, simplified_name, name_stats)
        except UnidecodeError:
            pass
    return firstname_stats


def lower_simplify_other(raw_stats):
    other_stats = {'all': collections.defaultdict(int),
                   'firstname_initials': collections.defaultdict(lambda: collections.defaultdict(int)),
                   'lastname_initials': collections.defaultdict(lambda: collections.defaultdict(int))}
    for country, count in raw_stats['all'].items():
        other_stats['all'][country] += count
    for country, initials in raw_stats['firstname_initials'].items():
        for initial, count in initials.items():
            lowered_initial = initial.lower()
            other_stats['firstname_initials'][country][lowered_initial] += count
            try:
                simplified_name = unidecode(lowered_initial, errors='strict')
                if simplified_name != lowered_initial:
                    other_stats['lastname_initials'][country][simplified_name] += count
            except UnidecodeError:
                pass
    for country, initials in raw_stats['lastname_initials'].items():
        for initial, count in initials.items():
            lowered_initial = initial.lower()
            other_stats['lastname_initials'][country][lowered_initial] += count
            try:
                simplified_name = unidecode(lowered_initial, errors='strict')
                if simplified_name != lowered_initial:
                    other_stats['lastname_initials'][country][simplified_name] += count
            except UnidecodeError:
                pass
    return other_stats


firstnames = lower_simplify(firstnames)
lastnames = lower_simplify(lastnames)

json.dump(firstnames, open(f's_firstnames_10kn.json', 'w'), ensure_ascii=False, indent=2)
json.dump(lastnames, open(f's_lastnames_10kn.json', 'w'), ensure_ascii=False, indent=2)

other = json.load(open('other_10kn.json'))
other = lower_simplify_other(other)
json.dump(other, open(f's_other_10kn.json', 'w'), ensure_ascii=False, indent=2)
