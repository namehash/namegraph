from argparse import ArgumentParser
from typing import Optional, Callable, Iterable
from collections import defaultdict
from operator import itemgetter
from copy import deepcopy
from pathlib import Path
import json
import sys
import re

import numpy as np
import requests
import nltk

from gensim.models.keyedvectors import KeyedVectors
import gensim.downloader
from nltk.corpus import stopwords
from tqdm import tqdm

nltk.download('stopwords')

import myunicode

PROJECT_ROOT_DIR = Path(__name__).parent.parent
TOKEN_SEPARATOR = re.compile(r'[_ ]')
STOPWORDS = set(stopwords.words('english'))
SKIPPED_STOPWORDS = ['*', '#']
MODIFIERS = ['🏻', '🏼', '🏽', '🏾', '🏿', '♂', '♀', '🦱', '🦰', '🦳']
FORBIDDEN_MODIFIERS = [
    'light skin tone',
    'medium-light skin tone',
    'medium skin tone',
    'medium-dark skin tone',
    'dark skin tone',
    'beard',
    'bald',
    'blond hair',
    'curly hair',
    'red hair',
    'white hair',
    'man',
    'woman',
    'person',
    'girl',
    'boy',
]


def _ens_normalize(text: str) -> Optional[str]:
    try:
        return myunicode.ens_normalize(text)
    except ValueError:
        return None


def _emoji_name(emoji: str) -> Optional[str]:
    try:
        name = myunicode.emoji_name(emoji)
        return name.lower() if name else None
    except ValueError:
        return None


def download_emoji2names(remove_country_abbreviations: bool = False) -> dict[str, list[str]]:
    r = requests.get(f'https://raw.githubusercontent.com/muan/emojilib/main/dist/emoji-en-US.json')
    json_data = json.loads(r.text)

    # normalize emojis, some of them normalize to non-emojis
    for emoji in list(json_data.keys()):
        normalized_emoji = _ens_normalize(emoji)
        if normalized_emoji is None:
            del json_data[emoji]
        elif normalized_emoji != emoji:
            json_data[normalized_emoji] = json_data[emoji]
            del json_data[emoji]

        emoji_name = _emoji_name(emoji)

        if emoji_name is not None and ':' in emoji_name:
            basename, modifier_string = emoji_name.split(':')
            has_forbidden_modifiers = any([
                modifier.strip()
                for modifier in modifier_string.split(',')
                if modifier.strip() in FORBIDDEN_MODIFIERS
            ])

            if has_forbidden_modifiers:
                json_data[emoji] = json_data[emoji][1:]

    if remove_country_abbreviations:
        for emoji, names in json_data.items():
            name = _emoji_name(emoji)
            if name is not None and name.startswith('flag:'):
                json_data[emoji] = [name for name in names if len(name) >= 3]

    return json_data


def download_all_emojis2names() -> dict[str, list[str]]:
    emojis2names = dict()
    for emoji in myunicode.emoji_iterator():
        name = _emoji_name(emoji)
        if name is None:
            continue

        if emoji != _ens_normalize(emoji):
            continue

        if ':' in name:
            basename, modifier_string = name.split(':')
            modifiers = [
                modifier.strip()
                for modifier in modifier_string.split(',')
                if modifier.strip() not in FORBIDDEN_MODIFIERS
            ]

            emojis2names[emoji] = [basename] + modifiers
        else:
            emojis2names[emoji] = [name]

    return emojis2names


def merge_emoji2names(
        emoji2names: dict[str, list[str]],
        rest_of_emoji2names: dict[str, list[str]]
) -> dict[str, list[str]]:

    emoji2names = deepcopy(emoji2names)
    for emoji, names in rest_of_emoji2names.items():
        emoji2names[emoji] = list(set(emoji2names.get(emoji, [])) | set(names))
    return emoji2names


def is_valid_token(token: str, dictionary: Optional[set[str]] = None) -> bool:
    if not token or token in STOPWORDS and token not in SKIPPED_STOPWORDS:
        return False

    if myunicode.is_emoji(token):
        return False

    for forbidden_symbol in ['_', ' ', '.']:
        if forbidden_symbol in token:
            return False

    try:
        if myunicode.ens_normalize(token) != token:
            return False
    except ValueError:
        return False

    if dictionary is not None and token not in dictionary:
        return False

    return True


def normalize_names(emoji2names: dict[str, list[str]]) -> dict[str, list[str]]:
    emoji2normalized_names = dict()
    for emoji, names in emoji2names.items():
        normalized_names = []
        for name in names:
            for token in TOKEN_SEPARATOR.split(name):
                if is_valid_token(token):
                    normalized_names.append(token)

        emoji2normalized_names[emoji] = normalized_names
    return emoji2normalized_names


def invert_emoji2names_mapping(emoji2names: dict[str, list[str]]) -> dict[str, list[str]]:
    name2emojis = defaultdict(set)
    for emoji, names in emoji2names.items():
        for name in names:
            name2emojis[name].add(emoji)
    return {name: list(emojis) for name, emojis in name2emojis.items()}


def generate_synonyms(
        model: KeyedVectors,
        word: str,
        threshold: float,
        topn: Optional[int] = None
) -> list[tuple[str, float]]:

    synonyms: list[tuple[str, float]] = []

    similarities = model.vectors @ model[word]
    indices, = np.where(similarities > threshold)
    best_similarities = similarities[indices]

    sorted_similarities_idxs = np.argsort(best_similarities)[::-1]
    sorted_similarities = best_similarities[sorted_similarities_idxs]
    sorted_indices = indices[sorted_similarities_idxs]

    if topn is not None:
        sorted_similarities = sorted_similarities[:topn]
        sorted_indices = sorted_indices[:topn]

    for index, similarity in zip(sorted_indices, sorted_similarities):
        synonym = model.index_to_key[index].lower()
        if len(synonym) == 1 and synonym.isascii(): continue
        synonyms.append((synonym, 100.0 if synonym == word else similarity))

    return synonyms


def enhance_names(
        model: KeyedVectors,
        name2emojis: dict[str, list[str]],
        threshold: float = 0.5,
        topn: Optional[int] = None,
        dictionary: Optional[set[str]] = None
) -> dict[str, list[tuple[str, float]]]:

    enhanced_name2emojis: dict[str, dict[str, float]] = defaultdict(dict)
    for name, emojis in tqdm(name2emojis.items(), desc='generating synonyms'):
        if dictionary is not None and name not in dictionary:
            continue

        if name not in model:
            names = [(name, 100.0)]
        else:
            names = generate_synonyms(model, name, threshold, topn)

        for synonym, similarity in names:
            if is_valid_token(synonym, dictionary=dictionary):
                # print(f'GENERATING {synonym} AS A SYNONYM TO {name}')
                for emoji in emojis:
                    if similarity > enhanced_name2emojis[synonym].get(emoji, float('-inf')):
                        enhanced_name2emojis[synonym][emoji] = similarity
            else:
                # print('Skipping non-normalized synonym', synonym, file=sys.stderr)
                pass

    return {name: list(emojis.items()) for name, emojis in enhanced_name2emojis.items()}


def extract_emojis_from_w2v(
        model: KeyedVectors,
        threshold: float = 0.5,
        topn: Optional[int] = None,
        dictionary: Optional[set[str]] = None
) -> dict[str, list[tuple[str, float]]]:

    emoji2names: dict[str, list[tuple[str, float]]] = dict()
    for key, index in model.key_to_index.items():
        normalized_key = _ens_normalize(key)
        if normalized_key is None or not myunicode.is_emoji(normalized_key):
            continue

        emoji2names[normalized_key] = []
        for synonym, similarity in generate_synonyms(model, key, threshold, topn):
            normalized_synonym = _ens_normalize(synonym)
            if normalized_synonym is None \
                    or myunicode.is_emoji(normalized_synonym) \
                    or not is_valid_token(normalized_synonym, dictionary=dictionary):
                continue

            emoji2names[normalized_key].append((normalized_synonym, similarity))

    name2emojis: dict[str, list[tuple[str, float]]] = dict()
    for emoji, names in emoji2names.items():
        for name, similarity in names:
            name2emojis[name] = name2emojis.get(name, [])
            name2emojis[name].append((emoji, similarity))

    return name2emojis


def merge_name2emojis(
        n2e1: dict[str, list[tuple[str, float]]],
        n2e2: dict[str, list[tuple[str, float]]]
) -> dict[str, list[tuple[str, float]]]:

    n2e = {
        name: dict(emojis)
        for name, emojis in n2e1.items()
    }

    for name, emojis in n2e2.items():
        if name not in n2e:
            n2e[name] = dict(emojis)
            continue

        for emoji, similarity in emojis:
            if similarity > n2e[name].get(emoji, float('-inf')):
                n2e[name][emoji] = similarity

    return {name: list(emojis.items()) for name, emojis in n2e.items()}


def has_modifier(emoji: str) -> bool:
    return any([
        len(emoji) > 1 and modifier in emoji
        for modifier in MODIFIERS
    ])


def sort_name2emojis_by_similarity(
        model: KeyedVectors,
        name2emojis: dict[str, list[tuple[str, float]]],
        emoji2names: dict[str, list[str]],
        frequences: dict[str, int],
        original_emojis2names: dict[str, list[str]]
) -> dict[str, list[str]]:

    name2sorted_emojis = dict()
    for name, emojis in tqdm(name2emojis.items(), desc='sorting emojis per token'):
        # otherwise we do as planned
        emojis = [
            (emoji, ((1 if name in original_emojis2names.get(emoji, []) else 0),
                     similarity,
                     frequences.get(emoji, 0.0),
                     emoji))  # emoji string to make order deterministic, even if all the previous are the same
            for emoji, similarity in emojis
        ]
        sorted_emoji = sorted(emojis, key=itemgetter(1), reverse=True)
        name2sorted_emojis[name] = [emoji for emoji, similarity in sorted_emoji]

    return name2sorted_emojis


def load_emoji2canonical(filepath: str | Path) -> dict[str, str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        confusables = json.load(f)

    emoji2canonical = {
        emoji: canonical or emoji
        for emoji, (canonical, _) in confusables.items()
    }

    return emoji2canonical


def cluster_emojis(name2emojis: dict[str, list[str]], emoji2canonical: dict[str, str]) -> dict[str, list[str]]:
    new_name2emojis = dict()
    for name, emojis in tqdm(name2emojis.items(), 'clustering emojis'):
        present_clusters = set()
        first_time_order = []
        rest_order = []

        for emoji in emojis:
            # if emoji is not in the confusables, then it is canonical
            canonical = emoji2canonical.get(emoji, emoji)
            if canonical not in present_clusters:
                first_time_order.append(emoji)
            else:
                rest_order.append(emoji)

            present_clusters.add(canonical)

        new_name2emojis[name] = first_time_order + rest_order

    return new_name2emojis


def extract_gold_mapping(name2emojis: dict[str, list[str]] | dict[str, dict[str, list[str]]]) -> dict[str, list[str]]:
    if not name2emojis:
        return dict()

    if isinstance(list(name2emojis.values())[0], dict):
        return {
            key: value.get('green', [])
            for key, value in name2emojis.items()
        }

    return name2emojis


def override_mapping(name2emojis: dict[str, list[str]], override: dict[str, list[str]]) -> dict[str, list[str]]:
    # could have been done in one line, but then it makes only a shallow copy
    new_name2emojis = deepcopy(name2emojis)
    new_name2emojis.update(override)
    return new_name2emojis


def append_mapping(name2emojis: dict[str, list[str]], append: dict[str, list[str]]) -> dict[str, list[str]]:
    new_name2emojis = deepcopy(name2emojis)
    for name, emojis in append.items():
        existing_emojis = new_name2emojis.get(name, [])
        new_name2emojis[name] = deepcopy(emojis)
        for emoji in existing_emojis:
            if emoji not in emojis:
                new_name2emojis[name].append(emoji)

    return new_name2emojis


def refactor_mapping(
        name2emojis: dict[str, list[str]],
        max_emojis_number: int = 1_000_000
):
    return {name: emojis[:max_emojis_number] for name, emojis in name2emojis.items() if emojis}


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--output', type=str, default=str(PROJECT_ROOT_DIR / 'data' / 'name2emoji.json'),
                        help='output filepath')
    parser.add_argument('--w2v', default='google',
                        help='word2vec model [google, twitter, built-in, own path]')
    parser.add_argument('--emoji_w2v', default=None,
                        help='word2vec model for generating synonyms to emojis [twitter, own path], '
                             'not using if nothing passed')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='minimal similarity threshold')
    parser.add_argument('--emoji_threshold', type=float, default=0.5,
                        help='minimal similarity threshold for emojis')
    parser.add_argument('--topn', type=int, default=1000,
                        help='synonyms per word limit (if not passed - limit is 1000)')
    parser.add_argument('--emoji_topn', type=int, default=1000,
                        help='synonyms per emoji limit (if not passed - limit is 1000)')
    parser.add_argument('--max_emojis_number', type=int, default=1_000_000,
                        help='the limit of emojis per token in the final mapping')
    parser.add_argument('--both_words', action='store_true',
                        help='setting this flag obliges both the base word '
                             'and the synonym to be from the specific dictionary')
    parser.add_argument('--remove_country_abbreviations', action='store_true',
                        help='remove country abbreviations from the downloaded emojilib mapping')
    parser.add_argument('--overrides', type=str, nargs='+',
                        help='json files with overrides to the final result')
    parser.add_argument('--appends', type=str, nargs='+',
                        help='json files with appends to the final result (appends to the very start)')
    args = parser.parse_args()

    threshold = args.threshold
    topn = args.topn

    emoji_threshold = args.emoji_threshold
    emoji_topn = args.emoji_topn

    if args.both_words:
        with open(PROJECT_ROOT_DIR / 'data' / 'w2v-dictionary.txt', 'r', encoding='utf-8') as f:
            dictionary = set([line.strip().lower() for line in f.read().strip().split('\n')])
    else:
        dictionary = None

    # processing
    emoji2names = download_emoji2names(remove_country_abbreviations=args.remove_country_abbreviations)
    all_emojis2names = download_all_emojis2names()

    # remove non-emojis
    for emoji in list(emoji2names.keys()):
        if emoji not in all_emojis2names:
            print('Removing non-emoji', emoji, file=sys.stderr)
            del emoji2names[emoji]

    emoji2names = merge_emoji2names(emoji2names, all_emojis2names)
    # sys.exit()

    emoji2names_normalized = normalize_names(emoji2names)
    name2emojis = invert_emoji2names_mapping(emoji2names_normalized)

    # loading w2v models
    if args.w2v == 'google':
        model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
    elif args.w2v == 'twitter':
        model = gensim.downloader.load('glove-twitter-200', return_path=False)
    elif args.w2v == 'built-in':
        model = KeyedVectors.load(str(PROJECT_ROOT_DIR / 'data' / 'embeddings.pkl'))
    else:
        model = KeyedVectors.load_word2vec_format(args.w2v, binary=False)

    if args.emoji_w2v is None:
        emoji_model = None
    elif args.emoji_w2v == 'twitter':
        emoji_model = gensim.downloader.load('glove-twitter-200', return_path=False)
    else:
        emoji_model = KeyedVectors.load_word2vec_format(args.emoji_w2v, binary=False)

    model.init_sims(replace=True)
    if emoji_model is not None:
        emoji_model.init_sims(replace=True)

    # continuing processing
    enhanced_name2emojis = enhance_names(model, name2emojis, threshold=threshold, topn=topn, dictionary=dictionary)

    if emoji_model is not None:
        emoji_based_name2emojis = extract_emojis_from_w2v(emoji_model, threshold=emoji_threshold,
                                                          topn=emoji_topn, dictionary=dictionary)
        merged_name2emojis = merge_name2emojis(enhanced_name2emojis, emoji_based_name2emojis)
    else:
        merged_name2emojis = enhanced_name2emojis

    with open(PROJECT_ROOT_DIR / 'data' / 'ens-emoji-freq.json', 'r', encoding='utf-8') as f:
        frequencies = json.load(f)

    name2sorted_emojis = sort_name2emojis_by_similarity(
        model,
        merged_name2emojis,
        emoji2names_normalized,
        frequencies,
        all_emojis2names
    )

    emoji2canonical = load_emoji2canonical(PROJECT_ROOT_DIR / 'data' / 'grapheme_confusables.json')
    name2sorted_emojis = cluster_emojis(name2sorted_emojis, emoji2canonical)

    if args.overrides is not None:
        for overrides_path in args.overrides:
            with open(overrides_path, 'r', encoding='utf-8') as f:
                overrides_raw = json.load(f)
                overrides = extract_gold_mapping(overrides_raw)

            name2sorted_emojis = override_mapping(name2sorted_emojis, overrides)

    if args.appends is not None:
        for appends_path in args.appends:
            with open(appends_path, 'r', encoding='utf-8') as f:
                append = json.load(f)

            name2sorted_emojis = append_mapping(name2sorted_emojis, append)

    final_name2emojis = refactor_mapping(name2sorted_emojis, max_emojis_number=args.max_emojis_number)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(final_name2emojis, f, indent=2, ensure_ascii=False, sort_keys=True)
