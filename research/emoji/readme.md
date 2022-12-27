Run `./download.py -a` to download the required data.

# Experiments

emoji token - token created based on emoji name or emojilib keyword

### Gold mappings

* **vulgarisms** - set of emojis for vulgar words (mostly interested in **recall** - whether our mapping understands complex relations and subtle meanings)
* **whatsapp** - a specific mapping developed by whatsapp (everything is meaningful, but especially **recall** - do we cover human annotations)
* **short words** - manually annotated emojis from excel spreadsheet (**recall** is biased towards the **googlenews**, because the dataset was generated using it and no new emojis were added, still it has some value)

## 1. Emojilib mapping

Downloaded from [muan/emojilib](https://github.com/muan/emojilib/blob/main/dist/emoji-en-US.json)

|                 | recall | precision |     f1 |
|----------------:|-------:|----------:|-------:|
| **vulgrarisms** | 01.39% |   100.00% | 02.74% |
|    **whatsapp** | 25.08% |    46.70% | 32.63% |
| **short words** | 28.65% |    85.67% | 42.94% |

## 2. embeddings: googlenews

Mapping generated based on `GoogleNews-vectors-negative300.bin` and using [download_emojilib.py](../../download/download_emojilib.py) script

|                 | recall | precision |     f1 |
|----------------:|-------:|----------:|-------:|
| **vulgrarisms** | 04.17% |    08.57% | 05.61% |
|    **whatsapp** | 51.56% |    10.90% | 18.00% |
| **short words** | 98.80% |    34.29% | 50.91% |

## 3. embeddings: generator built-in

Mapping generated based on embeddings used in `W2VGenerator`and using [download_emojilib.py](../../download/download_emojilib.py) script

|                  | recall | precision |      f1 |
|-----------------:|-------:|----------:|--------:|
|  **vulgrarisms** | 08.33% |    00.13% |  00.26% |
|     **whatsapp** | 52.50% |    01.35% |  02.63% |
|  **short words** | 82.35% |    01.94% |  03.79% |

## 4. embeddings: twitter

Mapping generated based on `glove-twitter-200`and using [download_emojilib.py](../../download/download_emojilib.py) script

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    00.22% | 00.43% |
|     **whatsapp** | 56.14% |    02.16% | 04.16% |
|  **short words** | 90.74% |    03.39% | 06.54% |

## 5. embeddings: twitter, also add emojis from embeddings

Mapping generated based on `glove-twitter-200` and by adding emoji synonyms which are included in the model

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    00.22% | 00.43% |
|     **whatsapp** | 56.14% |    02.16% | 04.16% |
|  **short words** | 90.74% |    03.39% | 06.54% |

## 6. embeddings: fine-tuned twitter, also add emojis from embeddings

Same as 5, but using our own fine-tuned W2V model

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 11.11% |    00.59% | 01.12% |
|     **whatsapp** | 52.14% |    04.26% | 07.88% |
|  **short words** | 72.11% |    05.30% | 09.88% |

## 7. embeddings: googlenews, add emojis from fine-tuned twitter

Using different models for words synonyms - `GoogleNews-vectors-negative300.bin`, and for emoji synonyms - our own fine-tuned W2V model

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    11.48% | 10.53% |
|     **whatsapp** | 51.82% |    10.86% | 17.95% |
|  **short words** | 98.80% |    34.08% | 50.68% |

## 8. add mapping from embeddings only if both tokens are words
## 9. other min similarity parameter
## 10. limit the maximum number of emoji replacements for a given token