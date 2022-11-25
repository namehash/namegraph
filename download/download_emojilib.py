from collections import defaultdict
from pathlib import Path
from typing import Optional, Callable
import json
import re

import numpy as np
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from gensim.models.keyedvectors import KeyedVectors
import requests


PROJECT_ROOT_DIR = Path(__name__).parent.parent
TOKEN_SEPARATOR = re.compile(r'[_ ]')
STOPWORDS = set(stopwords.words('english'))
SKIPPED_STOPWORDS = ['*', '#']


def download_emoji2names() -> dict[str, list[str]]:
    r = requests.get(f'https://raw.githubusercontent.com/muan/emojilib/main/dist/emoji-en-US.json')
    json_data = json.loads(r.text)
    return json_data


def normalize_names(emoji2names: dict[str, list[str]]) -> dict[str, list[str]]:
    emoji2normalized_names = dict()
    for emoji, names in emoji2names.items():
        normalized_names = []
        for name in names:
            for token in TOKEN_SEPARATOR.split(name):
                if not token or token in STOPWORDS and token not in SKIPPED_STOPWORDS:
                    continue

                normalized_names.append(name)

        emoji2normalized_names[emoji] = normalized_names
    return emoji2normalized_names


def invert_emoji2names_mapping(emoji2names: dict[str, list[str]]) -> dict[str, list[str]]:
    name2emojis = defaultdict(list)
    for emoji, names in emoji2names.items():
        for name in names:
            name2emojis[name].append(emoji)
    return dict(name2emojis)


def is_valid_name(name: str) -> bool:
    return '_' not in name and ' ' not in name


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


def enhance_names(name2emojis: dict[str, list[str]], threshold: float = 0.5, topn: Optional[int] = None) -> dict[str, list[str]]:
    model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
    # model = KeyedVectors.load(str(Path(__file__).parent.parent / 'data' / 'embeddings.pkl'))
    model.init_sims(replace=True)

    enhanced_name2emojis: dict[str, dict[str, None]] = defaultdict(dict)
    for name, emojis in name2emojis.items():
        if name not in model:
            names = [name]
        else:
            names = generate_synonyms(model, name, threshold, topn)

        for synonym in names:
            if is_valid_name(synonym):
                print(f'GENERATING {synonym} AS A SYNONYM TO {name}')
                enhanced_name2emojis[synonym].update([(emoji, None) for emoji in emojis])

    return {name: list(emojis.keys()) for name, emojis in enhanced_name2emojis.items()}


if __name__ == '__main__':
    emoji2names = download_emoji2names()
    emoji2names_normalized = normalize_names(emoji2names)
    name2emojis = invert_emoji2names_mapping(emoji2names_normalized)
    enhanced_name2emojis = enhance_names(name2emojis, topn=20)

    with open(PROJECT_ROOT_DIR / 'data' / 'name2emoji.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_name2emojis, f, indent=2, ensure_ascii=False)
