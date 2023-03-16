from argparse import ArgumentParser
import json
import jsonlines

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

    category = wiki_wiki.page(category_name, unquote=True)
    for member in category.categorymembers.values():
        if member.ns == wikipediaapi.Namespace.CATEGORY:
            continue  # TODO currently not checking subcategories
        else:  # TODO add WikiData type verification
            members.add(member.title)  # TODO do we need anything else apart from title?

    return list(members)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('input', help='JSON file to lists')
    parser.add_argument('output', help='JSONL file for the output collections')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        lists = json.load(f)

    with jsonlines.open(args.output, mode='w') as writer:
        for wikilist in tqdm.tqdm(lists):
            category_id = wikilist['category'].split('/')[-1]
            en_label = wikilist["category_wiki"].split('/')[-1]

            try:
                members = category_members(en_label)
                wikilist['members'] = members
                writer.write(wikilist)
            except KeyError as e:
                print(e)
                print(en_label, category_id)
