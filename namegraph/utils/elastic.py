from elasticsearch import Elasticsearch


def connect_to_elasticsearch(
        scheme: str,
        host: str,
        port: int,
        username: str,
        password: str,
) -> Elasticsearch:
    return Elasticsearch(
        hosts=[{
            'scheme': scheme,
            'host': host,
            'port': port
        }],
        http_auth=(username, password),
        http_compress=True,
        request_timeout=10,
    )


def index_exists(elastic: Elasticsearch, index_name: str) -> bool:
    return elastic.indices.exists(index=index_name)
