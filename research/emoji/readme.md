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
|    **whatsapp** | 28.73% |    46.70% | 35.50% |
| **short words** | 28.65% |    85.67% | 42.94% |

## 2. embeddings: googlenews

Mapping generated based on `GoogleNews-vectors-negative300.bin` and using [download_emojilib.py](../../download/download_emojilib.py) script

|                 | recall | precision |     f1 |
|----------------:|-------:|----------:|-------:|
| **vulgrarisms** | 04.17% |    08.57% | 05.61% |
|    **whatsapp** | 59.70% |    10.90% | 18.44% |
| **short words** | 98.80% |    34.29% | 50.91% |

## 3. embeddings: generator built-in

Mapping generated based on embeddings used in `W2VGenerator`and using [download_emojilib.py](../../download/download_emojilib.py) script

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 08.33% |    00.13% | 00.26% |
|     **whatsapp** | 60.80% |    01.35% | 02.64% |
|  **short words** | 82.35% |    01.94% | 03.79% |

## 4. embeddings: twitter

Mapping generated based on `glove-twitter-200`and using [download_emojilib.py](../../download/download_emojilib.py) script

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    00.22% | 00.43% |
|     **whatsapp** | 65.01% |    02.16% | 04.18% |
|  **short words** | 90.74% |    03.39% | 06.54% |

## 5. embeddings: twitter, also add emojis from embeddings

Mapping generated based on `glove-twitter-200` and by adding emoji synonyms which are included in the model

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    00.22% | 00.43% |
|     **whatsapp** | 65.01% |    02.16% | 04.18% |
|  **short words** | 90.74% |    03.39% | 06.54% |

## 6. embeddings: fine-tuned twitter, also add emojis from embeddings

Same as 5, but using our own fine-tuned W2V model

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 11.11% |    00.59% | 01.12% |
|     **whatsapp** | 60.38% |    04.26% | 07.96% |
|  **short words** | 72.11% |    05.30% | 09.88% |

## 7. embeddings: googlenews, add emojis from fine-tuned twitter

Using different models for words synonyms - `GoogleNews-vectors-negative300.bin`, and for emoji synonyms - our own fine-tuned W2V model

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    11.48% | 10.53% |
|     **whatsapp** | 60.01% |    10.86% | 18.39% |
|  **short words** | 98.80% |    34.08% | 50.68% |

## 8. add mapping from embeddings only if both tokens are words

### 8.1. based on googlenews (2)

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 04.17% |    09.38% | 05.77% |
|     **whatsapp** | 57.85% |    10.82% | 18.23% |
|  **short words** | 98.58% |    34.74% | 51.38% |

### 8.2. based on googlenews with emojis (7)

|                  | recall | precision |     f1 |
|-----------------:|-------:|----------:|-------:|
|  **vulgrarisms** | 09.72% |    12.07% | 10.77% |
|     **whatsapp** | 58.04% |    10.79% | 18.20% |
|  **short words** | 98.58% |    34.53% | 51.14% |

## 9. other min similarity and topn parameter

Based on googlenews and our own w2v for emoji synonyms, both tokens must be words

#### vulgarisms

<table>
    <tr><th rowspan="2"></th>       <th colspan="3">threshold=0.5</th>               <th colspan="3">threshold=0.53</th>              <th colspan="3">threshold=0.55</th>              <th colspan="3">threshold=0.57</th>              <th colspan="3">threshold=0.6</th>               <th colspan="3">threshold=0.62</th>             </tr>
    <tr>                            <th>recall</th><th>precision</th><th>f1</th>     <th>recall</th><th>precision</th><th>f1</th>     <th>recall</th><th>precision</th><th>f1</th>     <th>recall</th><th>precision</th><th>f1</th>     <th>recall</th><th>precision</th><th>f1</th>     <th>recall</th><th>precision</th><th>f1</th>    </tr>
    <tr><th>topn=15</th>            <td>05.56%</td> <td>30.77%</td> <td>09.41%</td>  <td>05.56%</td> <td>30.77%</td> <td>09.41%</td>  <td>05.56%</td> <td>30.77%</td> <td>09.41%</td>  <td>05.56%</td> <td>33.33%</td> <td>09.52%</td>  <td>05.56%</td> <td>36.36%</td> <td>09.64%</td>  <td>05.56%</td> <td>44.44%</td> <td>09.88%</td> </tr>
    <tr><th>topn=30</th>            <td>08.33%</td> <td>14.63%</td> <td>10.62%</td>  <td>08.33%</td> <td>15.79%</td> <td>10.91%</td>  <td>06.94%</td> <td>14.29%</td> <td>09.35%</td>  <td>06.94%</td> <td>23.81%</td> <td>10.75%</td>  <td>06.94%</td> <td>26.32%</td> <td>10.99%</td>  <td>06.94%</td> <td>33.33%</td> <td>11.49%</td> </tr>
    <tr><th>topn=40</th>            <td>08.33%</td> <td>13.04%</td> <td>10.17%</td>  <td>08.33%</td> <td>14.29%</td> <td>10.53%</td>  <td>06.94%</td> <td>13.16%</td> <td>09.09%</td>  <td>06.94%</td> <td>22.73%</td> <td>10.64%</td>  <td>06.94%</td> <td>25.00%</td> <td>10.87%</td>  <td>06.94%</td> <td>33.33%</td> <td>11.49%</td> </tr>
    <tr><th>topn=50</th>            <td>09.72%</td> <td>14.29%</td> <td>11.57%</td>  <td>09.72%</td> <td>15.91%</td> <td>12.07%</td>  <td>08.33%</td> <td>15.38%</td> <td>10.81%</td>  <td>08.33%</td> <td>26.09%</td> <td>12.63%</td>  <td>06.94%</td> <td>25.00%</td> <td>10.87%</td>  <td>06.94%</td> <td>33.33%</td> <td>11.49%</td> </tr>
    <tr><th>topn=75</th>            <td>09.72%</td> <td>11.29%</td> <td>10.45%</td>  <td>09.72%</td> <td>14.00%</td> <td>11.48%</td>  <td>08.33%</td> <td>15.00%</td> <td>10.71%</td>  <td>08.33%</td> <td>25.00%</td> <td>12.50%</td>  <td>06.94%</td> <td>25.00%</td> <td>10.87%</td>  <td>06.94%</td> <td>33.33%</td> <td>11.49%</td> </tr>
  
</table>

#### whatsapp

<table>
    <tr><th rowspan="2"></th>       <th colspan="3">threshold=0.5</th>                <th colspan="3">threshold=0.53</th>             <th colspan="3">threshold=0.55</th>             <th colspan="3">threshold=0.57</th>             <th colspan="3">threshold=0.6</th>              <th colspan="3">threshold=0.62</th>             </tr>
    <tr>                            <th>recall</th><th>precision</th><th>f1</th>      <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    </tr>
    <tr><th>topn=15</th>            <td>55.62%</td> <td>14.66%</td> <td>23.20%</td>   <td>55.28%</td> <td>15.22%</td> <td>23.87%</td> <td>54.78%</td> <td>16.80%</td> <td>25.71%</td> <td>54.33%</td> <td>17.31%</td> <td>26.26%</td> <td>53.66%</td> <td>19.34%</td> <td>28.43%</td> <td>52.92%</td> <td>22.32%</td> <td>31.40%</td> </tr>
    <tr><th>topn=30</th>            <td>56.98%</td> <td>12.32%</td> <td>20.26%</td>   <td>56.31%</td> <td>13.16%</td> <td>21.33%</td> <td>55.53%</td> <td>15.43%</td> <td>24.16%</td> <td>54.75%</td> <td>16.39%</td> <td>25.23%</td> <td>53.84%</td> <td>18.82%</td> <td>27.89%</td> <td>53.04%</td> <td>21.98%</td> <td>31.07%</td> </tr>
    <tr><th>topn=40</th>            <td>57.41%</td> <td>11.91%</td> <td>19.73%</td>   <td>56.66%</td> <td>12.84%</td> <td>20.93%</td> <td>55.80%</td> <td>15.10%</td> <td>23.76%</td> <td>54.97%</td> <td>16.10%</td> <td>24.91%</td> <td>53.91%</td> <td>18.70%</td> <td>27.77%</td> <td>53.09%</td> <td>21.87%</td> <td>30.98%</td> </tr>
    <tr><th>topn=50</th>            <td>57.63%</td> <td>11.42%</td> <td>19.06%</td>   <td>56.88%</td> <td>12.61%</td> <td>20.64%</td> <td>55.98%</td> <td>14.88%</td> <td>23.51%</td> <td>55.00%</td> <td>15.93%</td> <td>24.70%</td> <td>53.93%</td> <td>18.59%</td> <td>27.65%</td> <td>53.10%</td> <td>21.78%</td> <td>30.89%</td> </tr>
    <tr><th>topn=75</th>            <td>58.06%</td> <td>10.77%</td> <td>18.17%</td>   <td>57.08%</td> <td>12.28%</td> <td>20.21%</td> <td>56.13%</td> <td>14.57%</td> <td>23.14%</td> <td>55.10%</td> <td>15.69%</td> <td>24.43%</td> <td>53.96%</td> <td>18.49%</td> <td>27.55%</td> <td>53.12%</td> <td>21.72%</td> <td>30.84%</td> </tr>
  
</table>

#### short words

<table>
    <tr><th rowspan="2"></th>       <th colspan="3">threshold=0.5</th>                <th colspan="3">threshold=0.53</th>             <th colspan="3">threshold=0.55</th>             <th colspan="3">threshold=0.57</th>             <th colspan="3">threshold=0.6</th>              <th colspan="3">threshold=0.62</th>             </tr>
    <tr>                            <th>recall</th><th>precision</th><th>f1</th>      <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    <th>recall</th><th>precision</th><th>f1</th>    </tr>
    <tr><th>topn=15</th>            <td>76.91%</td> <td>41.50%</td> <td>53.91%</td>   <td>75.71%</td> <td>42.74%</td> <td>54.64%</td> <td>75.16%</td> <td>43.18%</td> <td>54.85%</td> <td>72.98%</td> <td>44.70%</td> <td>55.44%</td> <td>69.06%</td> <td>48.62%</td> <td>57.07%</td> <td>66.78%</td> <td>49.72%</td> <td>57.00%</td> </tr>
    <tr><th>topn=30</th>            <td>81.26%</td> <td>35.06%</td> <td>48.98%</td>   <td>78.76%</td> <td>37.44%</td> <td>50.75%</td> <td>78.10%</td> <td>38.04%</td> <td>51.16%</td> <td>74.51%</td> <td>42.30%</td> <td>53.96%</td> <td>69.61%</td> <td>47.58%</td> <td>56.52%</td> <td>66.88%</td> <td>48.96%</td> <td>56.54%</td> </tr>
    <tr><th>topn=40</th>            <td>83.33%</td> <td>33.97%</td> <td>48.26%</td>   <td>80.50%</td> <td>36.80%</td> <td>50.51%</td> <td>78.87%</td> <td>37.63%</td> <td>50.95%</td> <td>74.84%</td> <td>41.97%</td> <td>53.78%</td> <td>69.93%</td> <td>47.52%</td> <td>56.59%</td> <td>66.88%</td> <td>48.92%</td> <td>56.51%</td> </tr>
    <tr><th>topn=50</th>            <td>84.97%</td> <td>33.38%</td> <td>47.93%</td>   <td>81.59%</td> <td>36.22%</td> <td>50.17%</td> <td>79.52%</td> <td>37.28%</td> <td>50.76%</td> <td>75.49%</td> <td>41.62%</td> <td>53.66%</td> <td>70.15%</td> <td>47.39%</td> <td>56.57%</td> <td>66.99%</td> <td>48.81%</td> <td>56.47%</td> </tr>
    <tr><th>topn=75</th>            <td>98.69%</td> <td>34.41%</td> <td>51.03%</td>   <td>84.53%</td> <td>35.94%</td> <td>50.44%</td> <td>82.14%</td> <td>37.27%</td> <td>51.28%</td> <td>77.23%</td> <td>41.63%</td> <td>54.10%</td> <td>70.15%</td> <td>47.21%</td> <td>56.44%</td> <td>66.99%</td> <td>48.73%</td> <td>56.42%</td> </tr>
  
</table>


## 10. with gold overrides

Based on 8.2 using overrides. Full call is `python download/download_emojilib.py --w2v google --topn 75 --emoji_w2v research/emoji/emoji_w2v/emoji_w2v.bin --emoji_topn 50 --both_words --remove_country_abbreviations --overrides research/emoji/gold-mappings/short-words.json research/emoji/gold-mappings/vulgarisms.json`

|                  |  recall | precision |      f1 |
|-----------------:|--------:|----------:|--------:|
|  **vulgrarisms** | 100.00% |   100.00% | 100.00% |
|     **whatsapp** |  57.64% |    11.11% |  18.62% |
|  **short words** |  99.24% |    99.89% |  99.56% |

## 11. limit the maximum number of emoji replacements for a given token