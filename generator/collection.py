from __future__ import annotations

from typing import Any
import logging

import elasticsearch
from omegaconf import DictConfig

from generator.tokenization import WordNinjaTokenizer
from generator.utils.elastic import connect_to_elasticsearch, index_exists


logger = logging.getLogger('generator')


class Collection:
    def __init__(
            self,
            name: str,
            names: list[str],
            rank: float,
            score: float
            # TODO do we need those above? and do we need anything else?
    ):
        self.name = name
        self.names = names
        self.rank = rank
        self.score = score

    @classmethod
    def from_elasticsearch_hit(cls, hit: dict[str, Any]) -> Collection:
        return Collection(
            hit['_source']['data']['collection_name'],
            [x['normalized_name'] for x in hit['_source']['data']['names']],
            hit['_source']['template']['collection_rank'],
            hit['_score']
        )


class CollectionMatcher:
    def __init__(self, config: DictConfig):
        self.config = config
        self.tokenizer = WordNinjaTokenizer(config)
        self.index_name = config.elasticsearch.index

        try:
            self.elastic = connect_to_elasticsearch(
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
                                        "data.collection_name^2",
                                        "data.collection_name.exact^3",
                                        "data.names.normalized_name",
                                        "data.names.tokenized_name",
                                        "data.collection_description",
                                        "data.collection_keywords^2",
                                        # "template.collection_articles"
                                    ],
                                    "type": "cross_fields",
                                }
                            }
                        ],
                        "should": [
                            {
                                "rank_feature": {
                                    "field": "template.collection_rank",
                                    # "log": {
                                    #     "scaling_factor": 4
                                    # }
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

    def search(self, query: str, mode: str = 'featured', limit: int = 3) -> list[Collection]:
        if not self.active:
            return []

        query = query if mode == 'template' else ' '.join(self.tokenizer.tokenize(query)[0])
        return self._search(query, limit)
