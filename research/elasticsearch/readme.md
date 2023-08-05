/etc/elasticsearch/elasticsearch.yml:
http.max_content_length: 1000mb


### Presents suggestions for set of names only for collection generator.

python generate-report-only-collections.py  --host http://54.89.196.85

### Search collections connecting to Elasticsearch

./search.sh > report.html

### Search collections using collections API, test diversity algorithms

./search_client.sh > report_limit.html

### Search collections related to collection connecting to Elasticsearch

search_related_collections.py