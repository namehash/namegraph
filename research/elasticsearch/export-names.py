from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from tqdm import tqdm
import os

# Get credentials from environment variables
ES_SCHEME = os.getenv('ES_SCHEME', 'http')
ES_HOST = os.getenv('ES_HOST')
ES_PORT = int(os.getenv('ES_PORT'))
ES_USERNAME = os.getenv('ES_USERNAME')
ES_PASSWORD = os.getenv('ES_PASSWORD')
ES_INDEX = os.getenv('ES_INDEX')

# Initialize Elasticsearch client
es = Elasticsearch(
    hosts=[{
        'scheme': ES_SCHEME,
        'host': ES_HOST,
        'port': ES_PORT
    }],
    http_auth=(ES_USERNAME, ES_PASSWORD),
    timeout=60,
    http_compress=True,
)

# Query to get all documents
query = {
    "_source": ["data.names.normalized_name"],
    "query": {
        "match_all": {}
    }
}

# First, count total documents for progress bar
total_docs = es.count(index=ES_INDEX, body={"query": {"match_all": {}}})["count"]

# Initialize set to store unique names
unique_names = set()

# Scan through all documents with progress bar
print("Scanning documents...")
with tqdm(total=total_docs, desc="Processing documents") as pbar:
    for doc in scan(es, query=query, index=ES_INDEX):
        if "data" in doc["_source"] and "names" in doc["_source"]["data"]:
            names = doc["_source"]["data"]["names"]
            for name in names:
                if "normalized_name" in name:
                    unique_names.add(name["normalized_name"])
        pbar.update(1)

# Write unique names to file with progress bar
output_file = "exported_names.txt"
print(f"\nWriting {len(unique_names)} unique names to {output_file}...")
with open(output_file, "w", encoding="utf-8") as f:
    for name in tqdm(unique_names, desc="Writing names"):
        f.write(f"{name}\n")

print(f"Export complete! {len(unique_names)} unique names written to {output_file}")
