# Downloaders

Check the dependencies of the used downloader, because they may differ from the runtime requirements. For example, `download_emojilib.py` uses `myunicode` library developed in the `label-inspector` repository


# download_emoji_freq.py

Counts number of names in `data/suggestable_domains.tsv` containing each emoji and saves it in `data/ens-emoji-freq.json`.

# download_emojilib.py

Generates emojis related to tokens.

1. For each emoji we obtain its official name.
2. For some emojis we append keywords from emojilib library.
3. All names are normalized by splitting them by space and excluding functional (stop) words.
4. For each emojis' name we generate related tokens using word2vec with similarity threshold 0.5 and topn=75. `topn` strongly reduces number of related tokens.
5. For each token sorting of emojis is performed:
   * emoji with exact match using official name is first
   * rest of emojis are sorted by similarity and frequency

Similarity is calculated between a token and emoji's names form 1st and 2nd points (max is taken). So frequency sorting is applied among emojis with the same names (keywords).

# Changes

## Frequency

Frequency obtained from adraffy.

"like": [
    "❤",
    "🧡",
    "💋",
    "💚",
    "💙",
    "😍",
    "💛",
    "💜",
    "💖",
    "😘",
    "💗",
    "👍",
    "🥰",
    "💕",
    "💘",
    "😄",
    "💞",
    "💓",
    "😻",

Frequency calculated by us.

"like": [
    "❤",
    "🧡",
    "💚",
    "😍",
    "💋",
    "💙",
    "💖",
    "💜",
    "💛",
    "😘",
    "👍",
    "💕",
    "💗",
    "💘",
    "🥰",
    "😄",
    "💞",
    "💓",
    "😻",