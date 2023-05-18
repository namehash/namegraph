
1. Attach to docker instance
docker exec -it elasticsearch bash

~2. Inside docker instance add the plugin~
./bin/elasticsearch-plugin install https://github.com/o19s/elasticsearch-learning-to-rank/releases/download/v1.5.8-es8.7.1/ltr-plugin-v1.5.8-es8.7.1.zip

2. Use docker/Dockerfile as build script for installing LTR plugin

3. http PUT localhost:9200/_ltr -a elastic:espass

4. Feature creation

* create feature based on the query params (WORKS)

http POST localhost:9200/_ltr/_featureset/template_collections featureset:='{"features": [
    {"name": "collection_name", "params": ["keywords"], "template_language": "mustache", "template": {"match": {"data.collection_name": "{{keywords}}" }} }
]}' validation:='{"params": {"keywords": "apple"}, "index": "collection-templates-1"}' -a elastic:espass

* create feature based on collection metadata (DONT WORK but has to be validated if it really works!)

http POST localhost:9200/_ltr/_featureset/template_collections featureset:='{"features": [
    {
        "name": "collection_rank", 
        "params": [], 
        "template": {
            "function_score": {
                "functions": [
                    {
                        "field_value_factor": {
                           "field": "template.collection_rank"
                        }
                    }
                ],
                "query": {
                    "match_all": {}
                } 
            }
        }
    }
]}' validation:='{"params": {}, "index": "collection-templates-1"}' -a elastic:espass

* create feature based rank_feature (WORKS!)

http POST localhost:9200/_ltr/_featureset/template_collections featureset:='{"features": [
    {
        "name": "collection_rank", 
        "params": [], 
        "template": {
            "rank_feature": {
                "field": "template.collection_rank"
            }
        }
    },
    {
        "name": "collection_name", 
        "params": ["keywords"], 
        "template": {
            "match": {
                "data.collection_name": "{{keywords}}"
            }
        }
    }
]}' validation:='{"params": {"keywords": "apple"}, "index": "collection-templates-1"}' -a elastic:espass



5. Feature engineering

* document-specific metric - min raw term position (yet maximum position is returned first...)
http POST localhost:9200/_search query:='{"match_explorer": {"type": "min_raw_tp", "query": {"match": {"data.collection_name": "english polish"}}}}' -a elastic:espass | jq '.hits.hits[]._score'

* index-specific metric - sum of IDFs
http POST localhost:9200/_search query:='{"match_explorer": {"type": "sum_classic_idf", "query": {"match": {"data.collection_name": "english polish"}}}}' -a elastic:espass | jq '.hits.max_score'

* reading collection metadata (DOESN'T WORK)
http POST localhost:9200/_search query:='{"function_score": {"functions":[{ "field_value_factor": {"field": "template.collection_rank", "missing": 0}} ], "query": {"match_all": {}} }}' -a elastic:espass | jless

6. Retrive computed features 

http POST localhost:9200/collection-templates-1/_search query:='{
        "bool": {
            "must": { "match": {"data.collection_name": "apple" } },
            "filter": [
                {
                    "sltr": {
                        "_name": "logged_featureset",
                        "featureset": "template_collections",
                        "params": {
                            "keywords": "apple"
                        }
                    }
                }
            ]
        }
    }' ext:='{
        "ltr_log": {
            "log_specs": {
                "name": "log_entry1",
                "named_query": "logged_featureset"
            }
        }
    }' -a elastic:espass | jq '.hits.hits[].fields'

    This returns features for the matching documents.