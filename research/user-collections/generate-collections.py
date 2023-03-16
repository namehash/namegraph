from argparse import ArgumentParser
import requests
import json

import tqdm
import wikipediaapi
from wikidata.client import Client


wikidata = Client()
wiki_wiki = wikipediaapi.Wikipedia(
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI
)


def category_members(category_name: str) -> list:
    members = set()

    category = wiki_wiki.page(category_name)
    for member in category.categorymembers.values():
        if member.ns == wikipediaapi.Namespace.CATEGORY:
            continue  # TODO currently not checking subcategories
        else:  # TODO add WikiData type verification
            members.add(member.title)  # TODO do we need anything else apart from title?

    return list(members)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('input', help='JSON file to lists')
    parser.add_argument('output', help='JSON file for the output collections')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        lists = json.load(f)

    collections: dict[str, list[str]] = dict()
    for wikilist in tqdm.tqdm(lists):
        category_id = wikilist['category'].split('/')[-1]
        wikidata_category = wikidata.get(category_id, load=True)

        try:
            en_label = wikidata_category.label['en']
        except KeyError as ex:
            print(f'skipped {wikidata_category.label} {wikidata_category.id}')
            continue

        members = category_members(en_label)
        collections[en_label] = members

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(collections, f, indent=2, ensure_ascii=False)
