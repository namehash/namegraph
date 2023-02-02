import collections
import glob
import csv
import json

from tqdm import tqdm

# with genders per country

# Works on data from https://drive.google.com/file/d/1wRQfw5EYpzulvRfHCGIUWB2am5JUYVGk/view?usp=sharing published on https://pypi.org/project/names-dataset/
dirpath = 'curate'
TOP_NAMES = 10000  # save top TOP_NAMES from each country
OUTPUT_DIR = 'stats10kn'

for path in tqdm(sorted(glob.glob(dirpath + '/*'))):
    print(path)
    firstname_stats = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
    lastname_stats = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
    other_stats = {'all': collections.defaultdict(int),
                   'firstname_initials': collections.defaultdict(lambda: collections.defaultdict(int)),
                   'lastname_initials': collections.defaultdict(lambda: collections.defaultdict(int))}
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in tqdm(reader):
            firstname, lastname, gender, country = row
            firstname_stats[firstname][country][gender] += 1
            lastname_stats[lastname][country][gender] += 1
            other_stats['all'][country] += 1
            if firstname: other_stats['firstname_initials'][country][firstname[0]] += 1
            if lastname: other_stats['lastname_initials'][country][lastname[0]] += 1

    firstname_stats = {k: v for k, v in sorted(firstname_stats.items(), reverse=True,
                                               key=lambda x: sum([sum(y.values()) for y in x[1].values()]))[:TOP_NAMES]}
    lastname_stats = {k: v for k, v in sorted(lastname_stats.items(), reverse=True,
                                              key=lambda x: sum([sum(y.values()) for y in x[1].values()]))[:TOP_NAMES]}
    json.dump(firstname_stats, open(f'{OUTPUT_DIR}/firstname_{country}.json', 'w'))
    json.dump(lastname_stats, open(f'{OUTPUT_DIR}/lastname_{country}.json', 'w'))
    json.dump(other_stats, open(f'{OUTPUT_DIR}/other_{country}.json', 'w'))
