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
            names: list[str],
            namehashes: list[str],
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
        self.namehashes = namehashes
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
            title=hit['fields']['data.collection_name'][0],
            names=hit['fields']['normalized_names'],
            namehashes=hit['fields']['namehashes'],
            tokenized_names=[tuple(tokens) for tokens in hit['fields']['tokenized_names']],
            name_types=hit['fields']['collection_types'],
            rank=hit['fields']['template.collection_rank'][0],
            score=hit['_score'],
            owner=hit['fields']['metadata.owner'][0],
            number_of_names=hit['fields']['metadata.members_count'][0],
            collection_id=hit['fields']['metadata.id'][0],
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

    def _search_related(
            self,
            query: str,
            max_limit: int,
            name_diversity_ratio: Optional[float] = None,
            max_per_type: Optional[int] = None,
            limit_names: Optional[int] = 50
    ) -> tuple[list[Collection], dict]:

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None

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
                "size": max_limit if not apply_diversity else max_limit * 3,
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
                            "source": f"params['_source'].data.names.stream()" \
                                      + limit_names_script \
                                      + ".map(p -> p.normalized_name)" \
                                      + ".collect(Collectors.toList())"
                        }
                    },
                    "namehashes": {
                        "script": {
                            "source": f"params['_source'].template.names.stream()" \
                                      + limit_names_script \
                                      + ".map(p -> p.namehash)" \
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
        es_response_metadata = {'n_total_hits': response["hits"]['total']['value']}

        collections = [Collection.from_elasticsearch_hit(hit) for hit in hits]

        if not apply_diversity:
            return collections[:max_limit], es_response_metadata

        # diversify collections
        diversified = []
        penalized_collections: list[tuple[float, Collection]] = []

        # names cover
        used_names = set()

        # types cover
        used_types = defaultdict(int)

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
                return diversified, es_response_metadata

        # if we haven't reached the max limit, pad with penalized collections until we reach the max limit
        penalized_collections: list[Collection] = [
            collection
            for _, collection in sorted(penalized_collections, key=itemgetter(0), reverse=True)
        ]

        return diversified + penalized_collections[:max_limit - len(diversified)], es_response_metadata

    def search_by_string(
            self,
            query: str,
            mode: str,
            max_related_collections: int = 3,
            min_other_collections: int = 3,
            max_other_collections: int = 3,
            max_total_collections: int = 6,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: Optional[int] = 10
    ) -> tuple[list[Collection], dict]:

        if not self.active:
            return [], {}

        tokenized_query = ' '.join(self.tokenizer.tokenize(query)[0])
        if tokenized_query != query:
            # query = f'"{query}" OR "{tokenized_query}"'
            query = f'{query} {tokenized_query}'

        try:
            return self._search_related(
                query=query,
                max_limit=max_related_collections,
                name_diversity_ratio=name_diversity_ratio,
                max_per_type=max_per_type,
                limit_names=limit_names
            )
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed: {ex}')
            return [], {}

    def search_by_collection(
            self,
            collection_id: str,
            max_related_collections: int = 3,
            min_other_collections: int = 3,
            max_other_collections: int = 3,
            max_total_collections: int = 6,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: Optional[int] = 10
    ) -> tuple[list[Collection], dict]:

        if not self.active:
            return [], {}

        try:
            return self._search_related(collection_id, max_related_collections)  # TODO
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed: {ex}')
            return [], {}

    def get_collections_membership_count_for_name(self, normalized_name: str) -> int:
        response = self.elastic.count(
            index=self.index_name,
            body={
                  "query": {
                    "bool": {
                      "filter": [
                        {"term": {"data.names.normalized_name": normalized_name}},
                        {"term": {"data.public": True}}
                      ]
                    }
                  }
                },
        )

        return response['count']


    def get_collections_membership_list_for_name(self, normalized_name: str, n_top_names: int) -> list:
        response = self.elastic.search(
            index=self.index_name,
            body={
              "query": {
                "bool": {
                  "filter": [
                    {
                      "term": {
                        "data.names.normalized_name": normalized_name
                      }
                    },
                    {
                      "term": {
                        "data.public": True
                      }
                    }
                  ],
                  "should": [
                    {
                        "rank_feature": {
                            "field": "metadata.members_count"
                        }
                    },
                    {
                        "rank_feature": {
                            "field": "template.members_system_interesting_score_median"
                        }
                    },
                    {
                        "rank_feature": {
                            "field": "template.valid_members_ratio"
                        }
                    },
                    {
                        "rank_feature": {
                            "field": "template.nonavailable_members_ratio",
                            "boost": 10
                        }
                    }
                  ]
                }
              },
              "_source": False,
              "fields": [
                  "data.collection_name",
                  "metadata.owner",
                  "metadata.modified",
                  "metadata.members_count",
                  "metadata.id"
              ],
              "script_fields": {
                "names": {
                  "script": {
                    "source": f"params['_source'].data.names.stream().map(p -> p.normalized_name).collect(Collectors.toList())"
                  }
                }
              }
            }
    )

        found_collections = [  # todo: fill the rest for the collection (names, rank, score)
            {
                'title': hit['fields']['data.collection_name'][0],
                # 'names'
                'owner': hit['fields']['metadata.owner'][0],
                'number_of_names': hit['fields']['metadata.members_count'][0],
                # 'rank'
                # 'score'
                'collection_id': hit['fields']['metadata.id'][0],
                'last_updated_timestamp': hit['fields']['metadata.modified'][0],
                'top_names_list': hit['fields']['names'][:n_top_names]
            }
            for hit in response['hits']['hits']
        ]

        return found_collections
