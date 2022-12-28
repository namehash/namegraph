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


def _ens_normalize(text: str) -> Optional[str]:
    try:
        return myunicode.ens_normalize(text)
    except ValueError:
        return None


def download_emoji2names() -> dict[str, list[str]]:
    r = requests.get(f'https://raw.githubusercontent.com/muan/emojilib/main/dist/emoji-en-US.json')
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

    return json_data


def download_all_emojis2names() -> dict[str, list[str]]:
    emojis2names = dict()
    for emoji in myunicode.emoji_iterator():
        try:
            name = myunicode.emoji_name(emoji)
        except ValueError:
            continue
        try:
            if emoji != myunicode.ens_normalize(emoji): continue
        except ValueError:
            continue

        emojis2names[emoji] = [name]
    return emojis2names


def merge_emoji2names(emoji2names: dict[str, list[str]], rest_of_emoji2names: dict[str, list[str]]) -> dict[
    str, list[str]]:
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


def generate_synonyms(model: KeyedVectors,
                      word: str,
                      threshold: float,
                      topn: Optional[int] = None) -> list[tuple[str, float]]:

    synonyms: list[tuple[str, float]] = []

    similarities = model.vectors @ model[word]
    indices, = np.where(similarities > threshold)
    best_similarities = similarities[indices]

    sorted_similarities = np.argsort(best_similarities)[::-1]
    sorted_indices = indices[sorted_similarities]

    if topn is not None:
        sorted_similarities = sorted_similarities[:topn]
        sorted_indices = sorted_indices[:topn]

    for index, similarity in zip(sorted_indices, sorted_similarities):
        synonym = model.index_to_key[index].lower()
        if len(synonym) == 1 and synonym.isascii(): continue
        synonyms.append((synonym, 100.0 if synonym == word else similarity))

    return synonyms


def enhance_names(model: KeyedVectors,
                  name2emojis: dict[str, list[str]],
                  threshold: float = 0.5,
                  topn: Optional[int] = None,
                  dictionary: Optional[set[str]] = None) -> dict[str, list[tuple[str, float]]]:

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


def extract_emojis_from_w2v(model: KeyedVectors,
                            threshold: float = 0.5,
                            topn: Optional[int] = None,
                            dictionary: Optional[set[str]] = None) -> dict[str, list[tuple[str, float]]]:

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


def merge_name2emojis(n2e1: dict[str, list[tuple[str, float]]],
                      n2e2: dict[str, list[tuple[str, float]]]) -> dict[str, list[tuple[str, float]]]:

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


def sort_name2emojis_by_similarity(
        model: KeyedVectors,
        name2emojis: dict[str, list[tuple[str, float]]],
        emoji2names: dict[str, list[str]],
        frequences: dict[str, int],
        original_emojis2names: dict[str, list[str]]
) -> dict[str, list[str]]:

    def best_similarity(base: str, words: list[str]) -> float:
        similarities = []
        for word in words:
            # if the base is among the words from emojilib we consider it as superior factor
            if base == word:
                return 100.0

            if word in model:
                similarity = model.similarity(base, word)
                similarities.append(similarity)
        return max(similarities)

    name2sorted_emojis = dict()
    for name, emojis in tqdm(name2emojis.items(), desc='sorting emojis per token'):
        # if base is not in the model we cannot compare it :(
        # if name not in model:
        #     # name2sorted_emojis[name] = emojis
        #     # sort just by frequency
        #     print('Token not in model', name, emojis, file=sys.stderr)
        #     emojis = [(emoji, frequences.get(emoji, 0.0)) for emoji in emojis]
        #     sorted_emoji = sorted(emojis, key=itemgetter(1), reverse=True)
        #     name2sorted_emojis[name] = [emoji for emoji, similarity in sorted_emoji]
        #     continue

        # otherwise we do as planned
        emojis = [
            (emoji, ((1 if name in original_emojis2names.get(emoji, []) else 0),
                     similarity,
                     frequences.get(emoji, 0.0)))
            for emoji, similarity in emojis
        ]
        sorted_emoji = sorted(emojis, key=itemgetter(1), reverse=True)
        name2sorted_emojis[name] = [emoji for emoji, similarity in sorted_emoji]

    return name2sorted_emojis


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--output', type=str, default=str(PROJECT_ROOT_DIR / 'data' / 'name2emoji_by_frequency.json'),
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
    parser.add_argument('--both_words', action='store_true',
                        help='setting this flag obliges both the base word '
                             'and the synonym to be from the specific dictionary')
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
    emoji2names = download_emoji2names()
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

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(name2sorted_emojis, f, indent=2, ensure_ascii=False, sort_keys=True)
