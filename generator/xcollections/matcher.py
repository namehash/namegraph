from __future__ import annotations

from typing import Any, Optional, Literal
from collections import defaultdict
from operator import itemgetter
from time import perf_counter
import logging

import elastic_transport
import elasticsearch
from omegaconf import DictConfig

from generator.tokenization import WordNinjaTokenizer
from generator.xcollections.collection import Collection
from generator.xcollections.query_builder import ElasticsearchQueryBuilder
from generator.utils.elastic import connect_to_elasticsearch, index_exists
from generator.utils import Singleton

logger = logging.getLogger('generator')


class CollectionMatcher(metaclass=Singleton):
    def __init__(self, config: DictConfig):
        self.config = config
        self.tokenizer = WordNinjaTokenizer(config)
        self.index_name = config.elasticsearch.index

        self.ltr_feature_store = config.elasticsearch.ltr.feature_store
        self.ltr_feature_set = config.elasticsearch.ltr.feature_set
        self.ltr_model_name = config.elasticsearch.ltr.model_name
        self.ltr_window_size = config.elasticsearch.ltr.window_size

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

                # if more than `name_diversity_ratio` of the names have already been used, penalize the collection
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

    def _execute_query(
            self,
            query_params: dict,
            limit_names: int,
            script_names=False
    ) -> tuple[list[Collection], dict[str, Any]]:
        t_before = perf_counter()
        response = self.elastic.search(index=self.index_name, **query_params)
        time_elapsed = (perf_counter() - t_before) * 1000

        hits = response["hits"]["hits"]
        n_total_hits = response["hits"]['total']['value']
        es_response_metadata = {
            'n_total_hits': n_total_hits if n_total_hits <= 1000 else '1000+',
            'took': response['took'],
            'elasticsearch_communication_time': time_elapsed,
        }
        if script_names:
            collections = [Collection.from_elasticsearch_hit_script_names(hit, limit_names) for hit in hits]
        else:
            collections = [Collection.from_elasticsearch_hit(hit, limit_names) for hit in hits]
        return collections, es_response_metadata

    def _search_related(
            self,
            query: str,
            max_limit: int,
            fields: list[str],
            offset: int = 0,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = None,
            name_diversity_ratio: Optional[float] = None,
            max_per_type: Optional[int] = None,
            limit_names: int = 10,
    ) -> tuple[list[Collection], dict]:

        if sort_order == 'AI':
            sort_order = 'ES'

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None
        query_params = ElasticsearchQueryBuilder() \
            .add_query(query) \
            .add_filter('term', {'data.public': True}) \
            .set_sort_order(sort_order, field='data.collection_name.raw') \
            .add_limit(max_limit if not apply_diversity else max_limit * 3) \
            .add_offset(offset) \
            .add_rank_feature('template.collection_rank', boost=100) \
            .add_rank_feature('metadata.members_count') \
            .set_source(False) \
            .include_fields(fields) \
            .build_params()

        collections, es_response_metadata = self._execute_query(query_params, limit_names)

        if not apply_diversity:
            return collections[:max_limit], es_response_metadata

        diversified = self._apply_diversity(collections, max_limit, name_diversity_ratio, max_per_type)
        return diversified, es_response_metadata
