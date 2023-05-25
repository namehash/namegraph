from __future__ import annotations

from typing import Any, Union, Iterable
from collections import defaultdict
from operator import itemgetter
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
            names: list[str],
            tokenized_names: list[tuple[str]],
            name_types: list[str],
            rank: float,
            score: float
            # TODO do we need those above? and do we need anything else?
    ):
        self.title = title
        self.names = names
        self.tokenized_names = tokenized_names
        self.name_types = name_types
        self.rank = rank
        self.score = score

    @classmethod
    def from_elasticsearch_hit(cls, hit: dict[str, Any]) -> Collection:
        return cls(
            title=hit['_source']['data']['collection_name'],
            names=[x['normalized_name'] for x in hit['_source']['data']['names']],
            tokenized_names=[tuple(x['tokenized_name']) for x in hit['_source']['data']['names']],
            name_types=list(map(itemgetter(0), hit['_source']['template']['collection_types'])),
            rank=hit['_source']['template']['collection_rank'],
            score=hit['_score']
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

    def _search(self, query: str, limit: int, diversify_mode: str = 'none') -> list[Collection]:
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
                                        "data.collection_description^2",
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
                "size": limit if diversify_mode == 'none' else limit * 3,
            },
        )

        hits = response["hits"]["hits"]
        collections = [Collection.from_elasticsearch_hit(hit) for hit in hits]

        print(diversify_mode)
        if diversify_mode == 'none':
            return collections[:limit]

        # diversify collections
        diversified = []
        penalized_collections = []

        # names cover
        used_names = set()

        # types cover
        used_types = defaultdict(int)

        for collection in collections:
            if diversify_mode == 'names-cover' or diversify_mode == 'all':
                number_of_covered_names = len(set(collection.names) & used_names)

                # FIXME move `0.5` to request parameters
                # if more than 50% of the names have already been used, penalize the collection
                if number_of_covered_names / len(collection.names) < 0.5:
                    used_names.update(collection.names)
                else:
                    penalized_collections.append(collection)
                    continue

            if diversify_mode == 'types-cover' or diversify_mode == 'all':
                # FIXME move `3` to request parameters
                # if any of the types has occurred more than 3 times, penalize the collection
                if all([
                    used_types[name_type] < 3
                    for name_type in collection.name_types
                ]):

                    for name_type in collection.name_types:
                        used_types[name_type] += 1
                else:
                    penalized_collections.append(collection)
                    continue

            diversified.append(collection)

            if len(diversified) >= limit:
                return diversified

        return diversified + penalized_collections[:limit - len(diversified)]

    def search(
            self,
            query: Union[str, Iterable[str]],
            tokenized: bool = False,
            limit: int = 3,
            diversify_mode: str = 'none'
    ) -> list[Collection]:

        if not self.active:
            return []

        if tokenized and not isinstance(query, str):
            query = ' '.join(query)

        query = query if tokenized else ' '.join(self.tokenizer.tokenize(query)[0])
        try:
            return self._search(query, limit, diversify_mode=diversify_mode)
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed: {ex}')
            return []
