from elasticsearch import Elasticsearch


def connect_to_elasticsearch(
        host: str,
        port: int,
        username: str,
        password: str,
) -> Elasticsearch:
    return Elasticsearch(
        hosts=[{
            'scheme': 'https',
            'host': host,
            'port': port
        }],
        http_auth=(username, password),
        http_compress=True,
        #TODO add timeout
    )


def index_exists(elastic: Elasticsearch, index_name: str) -> bool:
    return elastic.indices.exists(index=index_name)
