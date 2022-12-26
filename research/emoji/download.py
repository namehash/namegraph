from argparse import ArgumentParser
from collections import defaultdict
import json

import requests

import myunicode


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}


def download_whatsapp(output_filepath: str) -> None:
    r = requests.get('https://web.whatsapp.com/emoji_suggestions/en.json', headers=HEADERS)
    json_data = json.loads(r.text)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


def download_emojilib(output_filepath: str) -> None:
    r = requests.get('https://raw.githubusercontent.com/muan/emojilib/main/dist/emoji-en-US.json', headers=HEADERS)
    json_data = json.loads(r.text)

    # normalize emojis, some of them normalize to non-emojis
    for emoji in list(json_data.keys()):
        try:
            normalized_emoji = myunicode.ens_normalize(emoji)
            if normalized_emoji != emoji:
                json_data[normalized_emoji] = json_data[emoji]
                del json_data[emoji]
        except ValueError:
            del json_data[emoji]

    name2emojis = defaultdict(set)
    for emoji, names in json_data.items():
        for name in names:
            name2emojis[name].add(emoji)
    name2emojis = {name: list(emojis) for name, emojis in name2emojis.items()}

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(name2emojis, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--all', '-a',
                        action='store_true',
                        help='download all the files')
    parser.add_argument('--whatsapp', '-w',
                        action='store_true',
                        help='download whatsapp gold mapping')
    parser.add_argument('--emojilib', '-e',
                        action='store_true',
                        help='download emojilib mapping')
    args = parser.parse_args()

    if args.all or args.whatsapp:
        download_whatsapp('gold-mappings/whatsapp.json')
    if args.all or args.emojilib:
        download_emojilib('mappings/01-emojilib.json')
