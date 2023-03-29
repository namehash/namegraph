/etc/elasticsearch/elasticsearch.yml:
http.max_content_length: 1000mb

time python populate.py category_members_collections.jsonl3
15m13,395s
time python populate.py list_links_collections.jsonl3
real	5m17,180s

python search.py "apple" "apples" "bmw" "hulk" "marvel" "marvel characters" "fruit" "fruits" "britney spears" "bmw car models" "cars" "football players" "cristiano ronaldo" "planets" "countries" "france" "switzerland" "bmw vehicles" > report.html
