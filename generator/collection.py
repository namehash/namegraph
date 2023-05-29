from __future__ import annotations

from typing import Any, Union, Iterable
import logging

import elastic_transport
import elasticsearch
from omegaconf import DictConfig

from generator.tokenization import WordNinjaTokenizer
from generator.utils.elastic import connect_to_elasticsearch, index_exists
from generator.utils import Singleton

logger = logging.getLogger('generator')


class Collection:
    def __init__(
            self,
            title: str,
            names: list[dict],
            tokenized_names: list[tuple[str]],
            rank: float,
            score: float,
            owner: str,
            number_of_names: int,
            collection_id: str,
            # TODO do we need those above? and do we need anything else?
    ):
        self.title = title
        self.names = names
        self.tokenized_names = tokenized_names
        self.rank = rank
        self.score = score
        self.owner = owner
        self.number_of_names = number_of_names
        self.collection_id = collection_id

    @classmethod
    def from_elasticsearch_hit(cls, hit: dict[str, Any]) -> Collection:
        return cls(
            title=hit['_source']['data']['collection_name'],
            names=[{'name': x['normalized_name'], 'namehash': x['namehash']} for x in
                   hit['_source']['template']['names']],
            tokenized_names=[tuple(x['tokenized_name']) for x in hit['_source']['data']['names']],
            rank=hit['_source']['template']['collection_rank'],
            score=hit['_score'],
            owner=hit['_source']['metadata']['owner'],
            number_of_names=len(hit['_source']['data']['names']),
            collection_id=hit['_source']['metadata']['id'],
        )


class CollectionMatcher(metaclass=Singleton):
    def __init__(self, config: DictConfig):
        self.config = config
        self.tokenizer = WordNinjaTokenizer(config)
        self.index_name = config.elasticsearch.index

        try:
            self.elastic = connect_to_elasticsearch(
                config.elasticsearch.scheme,
                config.elasticsearch.host,
                config.elasticsearch.port,
                config.elasticsearch.username,
                config.elasticsearch.password
            )

            self.active = index_exists(self.elastic, self.index_name)
            if not self.active:  # TODO should we raise Exception instead?
                logger.warning(f'Elasticsearch index {self.index_name} does not exist')

        except elasticsearch.ConnectionError as ex:
            logger.warning('Elasticsearch service is unavailable: ' + str(ex))
            self.active = False
        except elasticsearch.exceptions.AuthenticationException as ex:
            logger.warning('Elasticsearch authentication failed: ' + str(ex))
            self.active = False
        except elastic_transport.ConnectionTimeout as ex:
            logger.warning('Elasticsearch connection timed out: ' + str(ex))
            self.active = False
        except Exception as ex:
            logger.warning('Elasticsearch connection failed: ' + str(ex))
            self.active = False

    def _search(self, query: str, limit: int) -> list[Collection]:
        response = self.elastic.search(
            index=self.index_name,
            body={
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "data.collection_name^3",
                                        "data.collection_name.exact^3",
                                        # "data.collection_description^2",
                                        "data.collection_keywords^2",
                                        "data.names.normalized_name",
                                        "data.names.tokenized_name",
                                    ],
                                    "type": "cross_fields",
                                }
                            }
                        ],
                        "should": [
                            {
                                "rank_feature": {
                                    "field": "template.collection_rank",
                                    "boost": 100,
                                    # "log": {
                                    #     "scaling_factor": 4
                                    # }
                                }
                            },
                            {
                                "rank_feature": {
                                    "field": "metadata.members_count",
                                }
                            }
                        ]
                    }

                },
                "size": limit,
            },
        )

        hits = response["hits"]["hits"]
        return [Collection.from_elasticsearch_hit(hit) for hit in hits]

    def search_by_string(self, query: str,
                         mode: str,
                         max_related_collections: int = 3,
                         min_other_collections: int = 3,
                         max_other_collections: int = 3,
                         max_total_collections: int = 6,
                         name_diversity_ratio: float = 0.5,
                         max_per_type: int = 3,
                         limit_names: int = 10) -> list[Collection]:
        if not self.active:
            return []

        tokenized_query = ' '.join(self.tokenizer.tokenize(query)[0])
        if tokenized_query != query:
            # query = f'"{query}" OR "{tokenized_query}"'
            query = f'{query} {tokenized_query}'

        try:
            return self._search(query, max_related_collections)
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed: {ex}')
            return []

    def search_by_collection(self, collection_id: str,
                             max_related_collections: int = 3,
                             min_other_collections: int = 3,
                             max_other_collections: int = 3,
                             max_total_collections: int = 6,
                             name_diversity_ratio: float = 0.5,
                             max_per_type: int = 3,
                             limit_names: int = 10) -> list[
        Collection]:
        if not self.active:
            return []

        try:
            return self._search(collection_id, max_related_collections)  # TODO
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed: {ex}')
            return []
