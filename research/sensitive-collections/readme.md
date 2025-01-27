# Censoring Sensitive Collections

This document outlines the process for censoring sensitive collections:

1. We define a list of keywords that we want to censor.

```
nazi
SS personnel
criminals
fascists
nationalists
concentration camp personnel
gays
```

2. We execute a script that will search for these keywords in the Elasticsearch and create a CSV file with the results.

```bash
ES_HOST=xxx ES_PORT=xxx ES_USERNAME=xxx ES_PASSWORD=xxx ES_INDEX=xxx python collect-sensitive-collections.py \
  --input keywords.txt \
  --output sensitive.json
```

3. We review those results and after confirmation we map the names of the collections to their corresponding IDs.

`python map-sensitive-names.py --input sensitive.csv --mapping mapping.json --output ids-to-archive.txt`

4. We execute a script that will update the collections in the Elasticsearch by setting the archived flag to true for all the collections IDs that we want to censor.

```
ES_HOST=xxx ES_PORT=xxx ES_USERNAME=xxx ES_PASSWORD=xxx ES_INDEX=xxx python archive-sensitive-collections.py --input ids-to-archive.txt 
```
