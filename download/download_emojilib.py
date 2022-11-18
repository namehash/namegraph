from collections import defaultdict
from pathlib import Path
import json
import re

import numpy as np
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
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


def enhance_names(emoji2names: dict[str, list[str]], threshold: float = 0.5) -> dict[str, list[str]]:
    from gensim.models.keyedvectors import KeyedVectors

    model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
    model.init_sims(replace=True)

    emoji2enhanced_names = dict()
    for emoji, names in emoji2names.items():
        enhanced_names = []
        for name in names:
            if name not in model:
                enhanced_names.append(name)
            else:
                similarities = model.vectors @ model[name]
                indices, = np.where(similarities > threshold)
                best_similarities = similarities[indices]
                sorted_indices = indices[np.argsort(best_similarities)[::-1]]

                for index in sorted_indices:
                    enhanced_names.append(model.index_to_key[index])
                    print(f'GENERATING {model.index_to_key[index]} AS A SYNONYM TO {name}')

        emoji2enhanced_names[emoji] = enhanced_names

    return emoji2enhanced_names


def invert_emoji2names_mapping(emoji2names: dict[str, list[str]]) -> dict[str, list[str]]:
    name2emojis = defaultdict(list)
    for emoji, names in emoji2names.items():
        for name in names:
            name2emojis[name].append(emoji)
    return dict(name2emojis)


if __name__ == '__main__':
    emoji2names = download_emoji2names()
    emoji2names_normalized = normalize_names(emoji2names)
    emoji2names_enhanced = enhance_names(emoji2names_normalized)
    name2emojis = invert_emoji2names_mapping(emoji2names_enhanced)

    with open(PROJECT_ROOT_DIR / 'data' / 'name2emoji.json', 'w', encoding='utf-8') as f:
        json.dump(name2emojis, f, indent=2, ensure_ascii=False)
