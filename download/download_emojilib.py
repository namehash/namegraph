from typing import Optional, Callable, Iterable
from collections import defaultdict
from operator import itemgetter
from copy import deepcopy
from pathlib import Path
import json
import re

import numpy as np
import requests
import nltk

from gensim.models.keyedvectors import KeyedVectors
from nltk.corpus import stopwords
nltk.download('stopwords')

import myunicode


PROJECT_ROOT_DIR = Path(__name__).parent.parent
TOKEN_SEPARATOR = re.compile(r'[_ ]')
STOPWORDS = set(stopwords.words('english'))
SKIPPED_STOPWORDS = ['*', '#']


def download_emoji2names() -> dict[str, list[str]]:
    r = requests.get(f'https://raw.githubusercontent.com/muan/emojilib/main/dist/emoji-en-US.json')
    json_data = json.loads(r.text)
    return json_data


def download_all_emojis2names() -> dict[str, list[str]]:
    emojis2names = dict()
    for emoji in myunicode.emoji_iterator():
        try:
            name = myunicode.emoji_name(emoji)
        except ValueError:
            continue

        emojis2names[emoji] = [name]
    return emojis2names


def merge_emoji2names(emoji2names: dict[str, list[str]], rest_of_emoji2names: dict[str, list[str]]) -> dict[str, list[str]]:
    emoji2names = deepcopy(emoji2names)
    for emoji, names in rest_of_emoji2names.items():
        emoji2names[emoji] = list(set(emoji2names.get(emoji, [])) | set(names))
    return emoji2names


def is_valid_token(token: str) -> bool:
    if not token or token in STOPWORDS and token not in SKIPPED_STOPWORDS:
        return False

    if '_' in token or ' ' in token:
        return False

    try:
        if myunicode.ens_normalize(token) != token:
            return False
    except ValueError:
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


def generate_synonyms(model: KeyedVectors, word: str, threshold: float, topn: Optional[int] = None) -> list[str]:
    synonyms = []

    similarities = model.vectors @ model[word]
    indices, = np.where(similarities > threshold)
    best_similarities = similarities[indices]
    sorted_indices = indices[np.argsort(best_similarities)[::-1]]

    if topn is not None:
        sorted_indices = sorted_indices[:topn]

    for index in sorted_indices:
        synonym = model.index_to_key[index].lower()
        synonyms.append(synonym)
    return synonyms


def enhance_names(model: KeyedVectors, name2emojis: dict[str, list[str]], threshold: float = 0.5, topn: Optional[int] = None) -> dict[str, list[str]]:
    enhanced_name2emojis: dict[str, dict[str, None]] = defaultdict(dict)
    for name, emojis in name2emojis.items():
        if name not in model:
            names = [name]
        else:
            names = generate_synonyms(model, name, threshold, topn)

        for synonym in names:
            if is_valid_token(synonym):
                print(f'GENERATING {synonym} AS A SYNONYM TO {name}')
                enhanced_name2emojis[synonym].update([(emoji, None) for emoji in emojis])

    return {name: list(emojis.keys()) for name, emojis in enhanced_name2emojis.items()}


def sort_name2emojis(model: KeyedVectors, name2emojis: dict[str, list[str]], emoji2names: dict[str, list[str]]) -> dict[str, list[str]]:
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
    for name, emojis in name2emojis.items():
        # if base is not in the model we cannot compare it :(
        if name not in model:
            name2sorted_emojis[name] = emojis
            continue

        # otherwise we do as planned
        emojis = [(emoji, best_similarity(name, emoji2names[emoji])) for emoji in emojis]
        sorted_emoji = sorted(emojis, key=itemgetter(1), reverse=True)
        name2sorted_emojis[name] = [emoji for emoji, similarity in sorted_emoji]

    return name2sorted_emojis


if __name__ == '__main__':
    model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
    # model = KeyedVectors.load(str(Path(__file__).parent.parent / 'data' / 'embeddings.pkl'))
    model.init_sims(replace=True)

    # processing
    emoji2names = download_emoji2names()
    all_emojis2names = download_all_emojis2names()
    emoji2names = merge_emoji2names(emoji2names, all_emojis2names)

    emoji2names_normalized = normalize_names(emoji2names)
    name2emojis = invert_emoji2names_mapping(emoji2names_normalized)
    enhanced_name2emojis = enhance_names(model, name2emojis, topn=20)

    name2sorted_emojis = sort_name2emojis(model, enhanced_name2emojis, emoji2names_normalized)

    with open(PROJECT_ROOT_DIR / 'data' / 'name2emoji.json', 'w', encoding='utf-8') as f:
        json.dump(name2sorted_emojis, f, indent=2, ensure_ascii=False)
