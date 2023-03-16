from argparse import ArgumentParser
import json
import jsonlines

import tqdm
import wikipediaapi
from SPARQLWrapper import SPARQLWrapper, JSON
from wikidata.client import Client

wikidata = Client()
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")


def category_members2(category_name: str) -> list:
    members = set()

    category = wiki_wiki.page(category_name, unquote=True)
    for member in category.categorymembers.values():
        if member.ns == wikipediaapi.Namespace.CATEGORY:
            continue  # TODO currently not checking subcategories
        else:  # TODO add WikiData type verification
            members.add(member.title)  # TODO do we need anything else apart from title?

    return list(members)


def category_members(category_name: str, type: str) -> list:
    a = """SELECT ?item ?itemLabel ?type WHERE {{
      SERVICE wikibase:mwapi {{
         bd:serviceParam wikibase:api "Generator" .
         bd:serviceParam wikibase:endpoint "en.wikipedia.org" .
         bd:serviceParam mwapi:gcmtitle '{category_name}' .
         bd:serviceParam mwapi:generator "categorymembers" .
         bd:serviceParam mwapi:gcmprop "ids|title|type" .
         bd:serviceParam mwapi:gcmlimit "max" .
        ?item wikibase:apiOutputItem mwapi:item .
      }}
      ?item wdt:P31 wd:{type}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}""".format(category_name=category_name, type=type)

    sparql.setQuery(a)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    res = [item['itemLabel']['value'] for item in results['results']['bindings']]
    return res


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
            type = wikilist["type"].split('/')[-1]

            try:
                members = category_members(en_label, type)
                wikilist['members'] = members
                if members:
                    writer.write(wikilist)
                else:
                    print(f'no members with type {type}: {en_label}')
            except KeyError as e:
                print(e)
                print(en_label, category_id)
