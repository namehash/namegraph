from collections import defaultdict
from pathlib import Path
import json
import re

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
import requests


PROJECT_ROOT_DIR = Path(__name__).parent.parent
TOKEN_SEPARATOR = re.compile(r'[_ ]')
SKIPPED_STOPWORDS = ['*', '#']


if __name__ == '__main__':
    r = requests.get(f'https://raw.githubusercontent.com/muan/emojilib/main/dist/emoji-en-US.json')
    json_data = json.loads(r.text)
    STOPWORDS = set(stopwords.words('english'))

    name2emoji = defaultdict(dict)  # dict to preserve order
    for emoji, names in json_data.items():
        for name in names:
            for token in TOKEN_SEPARATOR.split(name):
                if not token or token in STOPWORDS and token not in SKIPPED_STOPWORDS:
                    continue
                name2emoji[token][emoji] = None

    name2emoji = {token: list(emojis.keys()) for token, emojis in name2emoji.items()}

    print(list(name2emoji.keys()))

    with open(PROJECT_ROOT_DIR / 'data' / 'name2emoji.json', 'w', encoding='utf-8') as f:
        json.dump(name2emoji, f, indent=2, ensure_ascii=False)
