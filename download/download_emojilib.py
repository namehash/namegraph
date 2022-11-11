from collections import defaultdict
from pathlib import Path
import json

import requests


PROJECT_ROOT_DIR = Path(__name__).parent.parent


if __name__ == '__main__':
    r = requests.get(f'https://raw.githubusercontent.com/muan/emojilib/main/dist/emoji-en-US.json')
    json_data = json.loads(r.text)

    name2emoji = defaultdict(list)
    for emoji, names in json_data.items():
        for name in names:
            name2emoji[name].append(emoji)

    with open(PROJECT_ROOT_DIR / 'data' / 'name2emoji.json', 'w', encoding='utf-8') as f:
        json.dump(name2emoji, f, indent=2, ensure_ascii=False)
