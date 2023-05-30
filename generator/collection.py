from __future__ import annotations

from typing import Any, Union, Iterable, Optional
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
            names: list[dict],
            tokenized_names: list[tuple[str]],
            name_types: list[str],
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
        self.name_types = name_types
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
            name_types=list(map(itemgetter(0), hit['_source']['template']['collection_types'])),
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

    def _search(
            self,
            query: str,
            limit: int,
            diversify_mode: str = 'none',
            limit_names: Optional[int] = 50
    ) -> list[Collection]:

        limit_names_script = f'.limit({limit_names})' if limit_names is not None else ''
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
                "size": limit if diversify_mode == 'none' else limit * 3,
                "fields": [
                    "data.collection_name",
                    "template.collection_rank",
                ],
                "_source": False,
                "script_fields": {
                    "normalized_names": {
                        "script": {
                            "source": f"params['_source'].data.names.stream()" \
                                      + limit_names_script \
                                      + ".map(p -> p.normalized_name)" \
                                      + ".collect(Collectors.toList())"
                        }
                    },
                    "tokenized_names": {
                        "script": {
                            "source": f"params['_source'].data.names.stream()" \
                                      + limit_names_script \
                                      + ".map(p -> p.tokenized_name)" \
                                      + ".collect(Collectors.toList())"
                        }
                    },
                    "collection_types": {
                        "script": {
                            "source": "params['_source'].template.collection_types.stream()"
                                      ".map(p -> p[0])"
                                      ".collect(Collectors.toList())"
                        }
                    }
                }
            },
        )

        hits = response["hits"]["hits"]
        collections = [Collection.from_elasticsearch_hit(hit) for hit in hits]

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

    def search_by_string(self, query: str,
                         mode: str,
                         min_limit: int = 10,
                         max_limit: int = 10,
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
            return self._search(query, max_limit)
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed: {ex}')
            return []

    def search_by_collection(
            self,
            collection_id: str,
            min_limit: int = 10,
            max_limit: int = 10,
            name_diversity_ratio: float = 0.5,
            max_per_type: int = 3,
            limit_names: int = 10
    ) -> list[Collection]:

        if not self.active:
            return []

        try:
            return self._search(collection_id, max_limit)  # TODO
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed: {ex}')
            return []
