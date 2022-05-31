time python3 research/affixes/find_prefixes.py data/domains.sorted.csv > research/affixes/eth_prefixes.txt
time python3 research/affixes/find_prefixes.py data/domains.sorted.csv -s > research/affixes/eth_suffixes.txt

time python3 research/affixes/find_prefixes.py research/data/alexa_million_names.txt > research/affixes/alexa_prefixes.txt
time python3 research/affixes/find_prefixes.py research/data/alexa_million_names.txt -s > research/affixes/alexa_suffixes.txt