Run `./download.py -a` to download the required data.

# Experiments

emoji token - token created based on emoji name or emojilib keyword

### Gold mappings

* **vulgarisms** - set of emojis for vulgar words (mostly interested in **recall** - whether our mapping understands complex relations and subtle meanings)
* **whatsapp** - a specific mapping developed by whatsapp (everything is meaningful, but especially **recall** - do we cover human annotations)
* **short words** - manually annotated emojis from excel spreadsheet (**recall** is biased towards the **googlenews**, because the dataset was generated using it and no new emojis were added, still it has some value)

## 1. Emojilib mapping

|                 | recall | precision |     f1 |
|----------------:|-------:|----------:|-------:|
| **vulgrarisms** | 01.39% |   100.00% | 02.74% |
|    **whatsapp** | 25.08% |    46.70% | 32.63% |
| **short words** | 28.65% |    85.67% | 42.94% |

## 2. embeddings: googlenews

|                 | recall | precision |     f1 |
|----------------:|-------:|----------:|-------:|
| **vulgrarisms** | 04.17% |    08.57% | 05.61% |
|    **whatsapp** | 51.56% |    10.90% | 18.00% |
| **short words** | 98.80% |    34.29% | 50.91% |

## 3. embeddings: generator built-in

|                  | recall | precision |      f1 |
|-----------------:|-------:|----------:|--------:|
|  **vulgrarisms** | 08.33% |    00.13% |  00.26% |
|     **whatsapp** | 52.50% |    01.35% |  02.63% |
|  **short words** | 82.35% |    01.94% |  03.79% |

## 4. embeddings: twitter

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    00.22% | 00.43% |
|     **whatsapp** | 56.14% |    02.16% | 04.16% |
|  **short words** | 90.74% |    03.39% | 06.54% |

## 5. embeddings: twitter, also add emojis from embeddings
## 6. embeddings: fine-tuned twitter, also add emojis from embeddings
## 7. add mapping from embeddings only if both tokens are words
## 8. other min similarity parameter
## 9. limit the maximum number of emoji replacements for a given token