from elasticsearch import Elasticsearch


def connect_to_elasticsearch(
        host: str,
        port: int,
        username: str,
        password: str,
) -> Elasticsearch:
    return Elasticsearch(
        hosts=[{
            'scheme': 'http',
            'host': host,
            'port': port
        }],
        http_auth=(username, password)
    )


def index_exists(elastic: Elasticsearch, index_name: str) -> bool:
    return elastic.indices.exists(index_name)
