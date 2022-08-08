# Wikipedia2vec

Embeddings need to be lowercased.

1. Download embeddings in text format: https://wikipedia2vec.github.io/wikipedia2vec/#pretrained-embeddings
2. Preprocess embeddings.

```
python prepare_embeddings.py enwiki_20180420_100d.txt enwiki_20180420_100d.txt.processed
```

3. Convert to pickle.

```
python convert.py enwiki_20180420_100d.txt.processed enwiki_20180420_100d.txt.processed.pkl
```