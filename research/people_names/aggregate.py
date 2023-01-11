import collections
import glob
import json

from tqdm import tqdm

dirpath = 'stats10kn'


def agg(stats, name, name_stats):
    for country, gender_counts in name_stats.items():
        for gender, count in gender_counts.items():
            stats[name][country][gender] += count


def agg_other(stats, country_stats):
    for country, count in country_stats['all'].items():
        stats['all'][country] += count
    for country, initials in country_stats['firstname_initials'].items():
        for initial, count in initials.items():
            stats['firstname_initials'][country][initial] += count
    for country, initials in country_stats['lastname_initials'].items():
        for initial, count in initials.items():
            stats['lastname_initials'][country][initial] += count


other_stats = {'all': collections.defaultdict(int),
               'firstname_initials': collections.defaultdict(lambda: collections.defaultdict(int)),
               'lastname_initials': collections.defaultdict(lambda: collections.defaultdict(int))}
for path in tqdm(sorted(glob.glob(dirpath + '/other*'))):
    print(path)
    data = json.load(open(path))
    agg_other(other_stats, data)
json.dump(other_stats, open(f'other_10kn.json', 'w'), ensure_ascii=False, indent=2)

firstname_stats = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
for path in tqdm(sorted(glob.glob(dirpath + '/firstname*'))):
    print(path)
    data = json.load(open(path))
    for name, name_stats in data.items():
        agg(firstname_stats, name, name_stats)
json.dump(firstname_stats, open(f'firstnames_10kn.json', 'w'), ensure_ascii=False, indent=2)

firstname_stats = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
for path in tqdm(sorted(glob.glob(dirpath + '/lastname*'))):
    print(path)
    data = json.load(open(path))
    for name, name_stats in data.items():
        agg(firstname_stats, name, name_stats)
json.dump(firstname_stats, open(f'lastnames_10kn.json', 'w'), ensure_ascii=False, indent=2)
