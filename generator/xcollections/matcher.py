from __future__ import annotations

from typing import Any, Union, Iterable, Optional
from collections import defaultdict
from operator import itemgetter
import logging

import elastic_transport
import elasticsearch
from omegaconf import DictConfig

from generator.tokenization import WordNinjaTokenizer
from generator.xcollections.collection import Collection
from generator.utils.elastic import connect_to_elasticsearch, index_exists
from generator.utils import Singleton

logger = logging.getLogger('generator')


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

    def _construct_request_body(
            self,
            query: str,
            limit_collections: int,
            limit_names: Optional[int],
            include_tokens: bool = False,
    ) -> dict[str, Any]:

        limit_names_subscript = f'.limit({limit_names})' if limit_names is not None else ''
        names_field = 'names' if limit_names is None or limit_names > 10 else 'top10_names'
        limit_names_script = f"params['_source'].template.{names_field}.stream(){limit_names_subscript}"

        body = {
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
            "size": limit_collections,
            "fields": [
                "data.collection_name",
                "template.collection_rank",
                "metadata.owner",
                "metadata.members_count",
                "metadata.id",
            ],
            "_source": False,
            "script_fields": {
                "normalized_names": {
                    "script": {
                        "source": limit_names_script \
                                  + ".map(p -> p.normalized_name)" \
                                  + ".collect(Collectors.toList())"
                    }
                },
                "namehashes": {
                    "script": {
                        "source": limit_names_script \
                                  + ".map(p -> p.namehash)" \
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
        }

        if include_tokens:
            body['script_fields']['tokenized_names'] = {
                "script": {
                    "source": "params['_source'].data.names.stream()" \
                              + limit_names_subscript \
                              + ".map(p -> p.tokenized_name)" \
                              + ".collect(Collectors.toList())"
                }
            }

        return body

    def _apply_diversity(
            self,
            collections: list[Collection],
            max_limit: int,
            name_diversity_ratio: Optional[float],
            max_per_type: Optional[int],
    ) -> list[Collection]:

        diversified = []
        penalized_collections: list[tuple[float, Collection]] = []

        used_names = set()  # names cover
        used_types = defaultdict(int)  # types cover

        for collection in collections:
            if name_diversity_ratio is not None:
                number_of_covered_names = len(set(collection.names) & used_names)

                # if more than `name_diversity_ration` of the names have already been used, penalize the collection
                if number_of_covered_names / len(collection.names) < name_diversity_ratio:
                    used_names.update(collection.names)
                else:
                    penalized_collections.append((collection.score * 0.8, collection))
                    continue

            if max_per_type is not None:
                # if any of the types has occurred more than `max_per_type` times, penalize the collection
                if all([
                    used_types[name_type] < max_per_type
                    for name_type in collection.name_types
                ]):

                    for name_type in collection.name_types:
                        used_types[name_type] += 1
                else:
                    penalized_collections.append((collection.score, collection))
                    continue

            diversified.append(collection)

            # if we reach the max limit, then return
            if len(diversified) >= max_limit:
                return diversified

        # if we haven't reached the max limit, pad with penalized collections until we reach the max limit
        penalized_collections: list[Collection] = [
            collection
            for _, collection in sorted(penalized_collections, key=itemgetter(0), reverse=True)
        ]

        return diversified + penalized_collections[:max_limit - len(diversified)]

    def _search_related(
            self,
            query: str,
            max_limit: int,
            name_diversity_ratio: Optional[float] = None,
            max_per_type: Optional[int] = None,
            limit_names: Optional[int] = 50,
            include_tokens: bool = False,
    ) -> tuple[list[Collection], dict]:

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None
        body = self._construct_request_body(
            query,
            max_limit if not apply_diversity else max_limit * 3,
            limit_names,
            include_tokens=include_tokens
        )

        response = self.elastic.search(index=self.index_name, body=body)

        hits = response["hits"]["hits"]
        es_response_metadata = {
            'n_total_hits': response["hits"]['total']['value'],
            'took': response['took'],
        }

        collections = [Collection.from_elasticsearch_hit(hit) for hit in hits]

        if not apply_diversity:
            return collections[:max_limit], es_response_metadata

        diversified = self._apply_diversity(collections, max_limit, name_diversity_ratio, max_per_type)
        return diversified, es_response_metadata
