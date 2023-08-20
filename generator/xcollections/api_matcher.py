from typing import Optional, Literal, Union
from time import perf_counter
import logging

from fastapi import HTTPException

from generator.xcollections.matcher import CollectionMatcher
from generator.xcollections.collection import Collection
from generator.xcollections.query_builder import ElasticsearchQueryBuilder
from .utils import get_names_script, get_namehashes_script


logger = logging.getLogger('generator')


class CollectionMatcherForAPI(CollectionMatcher):
    def search_by_string(
            self,
            query: str,
            mode: str,
            max_related_collections: int = 3,
            offset: int = 0,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = 'AI',
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: int = 10,
    ) -> tuple[list[Collection], dict]:

        query = query.strip()
        if ' ' not in query:
            tokenized_query = ' '.join(self.tokenizer.tokenize(query)[0])
            if tokenized_query != query:
                query = f'{query} {tokenized_query}'

        include_fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank', 'metadata.owner',
            'metadata.members_count', 'template.top10_names.normalized_name', 'template.top10_names.namehash',
            'template.collection_types', 'metadata.modified', 'data.avatar_emoji', 'data.avatar_image'
        ]

        query_fields = [
            'data.collection_name^3', 'data.collection_name.exact^3', 'data.collection_description',
            'data.collection_keywords^2', 'data.names.normalized_name', 'data.names.tokenized_name'
        ]

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None
        query_builder = ElasticsearchQueryBuilder() \
            .add_filter('term', {'data.public': True}) \
            .add_limit(max_related_collections if not apply_diversity else max_related_collections * 3) \
            .add_offset(offset) \
            .add_rank_feature('template.collection_rank', boost=100) \
            .set_source(False) \
            .include_fields(include_fields)

        if sort_order == 'AI':
            window_size = self.ltr_window_size.instant if mode == 'instant' else self.ltr_window_size.domain_detail

            query_params = query_builder \
                .add_query(query, fields=query_fields, type_='most_fields') \
                .add_rank_feature('metadata.members_rank_mean', boost=1) \
                .add_rank_feature('metadata.members_rank_median', boost=1) \
                .add_rank_feature('template.members_system_interesting_score_mean', boost=1) \
                .add_rank_feature('template.members_system_interesting_score_median', boost=1) \
                .add_rank_feature('template.valid_members_count', boost=1) \
                .add_rank_feature('template.invalid_members_count', boost=1) \
                .add_rank_feature('template.valid_members_ratio', boost=1) \
                .add_rank_feature('template.nonavailable_members_count', boost=1) \
                .add_rank_feature('template.nonavailable_members_ratio', boost=1) \
                .rescore_with_learning_to_rank(query,
                                               window_size=window_size,
                                               model_name=self.ltr_model_name,
                                               feature_set=self.ltr_feature_set,
                                               feature_store=self.ltr_feature_store,
                                               query_weight=0.001,
                                               rescore_query_weight=1000) \
                .build_params()
        else:
            query_params = query_builder \
                .add_query(query, fields=query_fields, type_='cross_fields') \
                .add_rank_feature('metadata.members_count') \
                .set_sort_order(sort_order, field='data.collection_name.raw') \
                .build_params()

        try:
            collections, es_response_metadata = self._execute_query(query_params, limit_names)

            if not apply_diversity:
                return collections[:max_related_collections], es_response_metadata

            diversified = self._apply_diversity(collections, max_related_collections,
                                                name_diversity_ratio, max_per_type)
            return diversified, es_response_metadata
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [by-string]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

    def get_collections_count_by_string(self, query: str, mode: str) -> tuple[Union[int, str], dict]:

        tokenized_query = ' '.join(self.tokenizer.tokenize(query)[0])
        if tokenized_query != query:
            query = f'{query} {tokenized_query}'

        query_fields = [
            'data.collection_name^3', 'data.collection_name.exact^3', 'data.collection_description',
            'data.collection_keywords^2', 'data.names.normalized_name', 'data.names.tokenized_name'
        ]

        query_params = ElasticsearchQueryBuilder() \
            .add_query(query, fields=query_fields, type_='cross_fields') \
            .add_filter('term', {'data.public': True}) \
            .add_rank_feature('template.collection_rank', boost=100) \
            .add_rank_feature('metadata.members_count') \
            .build_params()

        try:
            t_before = perf_counter()
            response = self.elastic.count(
                index=self.index_name,
                **query_params
            )
            time_elapsed = (perf_counter() - t_before) * 1000
        except Exception as ex:
            logger.error(f'Elasticsearch count failed [by-string]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        count = response['count']

        return count if count <= 1000 else '1000+', {'elasticsearch_communication_time': time_elapsed}

    def search_by_collection(
            self,
            collection_id: str,
            max_related_collections: int = 3,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: Optional[int] = 10,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = 'AI',
            offset: int = 0
    ) -> tuple[list[Collection], dict]:

        if sort_order == 'AI':
            sort_order = 'ES'

        fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank', 'metadata.owner',
            'metadata.members_count', 'template.top10_names.normalized_name', 'template.top10_names.namehash',
            'template.collection_types', 'metadata.modified', 'data.avatar_emoji', 'data.avatar_image'
        ]

        # find collection with specified collection_id
        id_match_params = (ElasticsearchQueryBuilder()
                           .set_term('metadata.id.keyword', collection_id)
                           .set_source(False)
                           .include_fields(fields)
                           .include_script_field('script_names', get_names_script(limit_names=100))
                           .include_script_field('script_namehashes', get_namehashes_script(limit_names=100))
                           .build_params())

        try:
            collections, es_response_metadata = self._execute_query(id_match_params, limit_names=100, script_names=True)
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [id-to-collection search]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        try:
            found_collection = collections[0]
        except IndexError as ex:
            logger.error(f'could not find collection with id {collection_id}', exc_info=True)
            raise HTTPException(status_code=404, detail=f"Collection with id={collection_id} not found.")

        es_time_first = es_response_metadata['took']
        es_comm_time_first = es_response_metadata['elasticsearch_communication_time']
        if es_response_metadata['n_total_hits'] > 1:
            logger.warning(f'more than 1 collection found with id {collection_id}')

        # search similar collections
        apply_diversity = name_diversity_ratio is not None or max_per_type is not None

        query_params = (ElasticsearchQueryBuilder()
                        .add_query(found_collection.title, boolean_clause='should', type_='cross_fields',
                                   fields=["data.collection_name^3", "data.collection_name.exact^3",
                                           'data.collection_keywords^2'])
                        .add_query(' '.join(found_collection.names), boolean_clause='should', type_='cross_fields',
                                   fields=["data.names.normalized_name"])
                        .add_filter('term', {'data.public': True})
                        .add_must_not('term', {"metadata.id.keyword": collection_id})
                        .add_rank_feature('template.collection_rank', boost=100)
                        .add_rank_feature('metadata.members_count')
                        .add_rank_feature('template.members_rank_mean')
                        .add_rank_feature('template.members_system_interesting_score_median')
                        .add_rank_feature('template.valid_members_ratio')
                        .add_rank_feature('template.nonavailable_members_ratio')
                        .set_source(False)
                        .include_fields(fields)
                        .set_sort_order(sort_order, field='data.collection_name.raw')
                        .add_limit(max_related_collections if not apply_diversity else max_related_collections * 3)
                        .add_offset(offset)
                        .build_params())

        try:
            collections, es_response_metadata = self._execute_query(query_params, limit_names)
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [collection-to-collections search]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        es_response_metadata['took'] += es_time_first
        es_response_metadata['elasticsearch_communication_time'] += es_comm_time_first

        if not apply_diversity:
            return collections, es_response_metadata

        diversified = self._apply_diversity(collections, max_related_collections, name_diversity_ratio, max_per_type)
        return diversified, es_response_metadata

    def get_collections_membership_count_for_name(self, name_label: str) -> tuple[Union[int, str], dict]:

        query_params = ElasticsearchQueryBuilder() \
            .add_filter('term', {'data.names.normalized_name': name_label}) \
            .add_filter('term', {'data.public': True}) \
            .build_params()

        try:
            t_before = perf_counter()
            response = self.elastic.count(
                index=self.index_name,
                **query_params
            )
            time_elapsed = (perf_counter() - t_before) * 1000
        except Exception as ex:
            logger.error(f'Elasticsearch count failed [by-member]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        count = response['count']

        return count if count <= 1000 else '1000+', {'elasticsearch_communication_time': time_elapsed}

    def get_collections_membership_list_for_name(
            self,
            name_label: str,
            limit_names: int = 10,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = 'AI',
            max_results: int = 3,
            offset: int = 0
    ) -> tuple[list[Collection], dict]:

        fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank', 'metadata.owner',
            'metadata.members_count', 'template.top10_names.normalized_name', 'template.top10_names.namehash',
            'template.collection_types', 'metadata.modified', 'data.avatar_emoji', 'data.avatar_image'
        ]

        if sort_order == 'AI':
            sort_order = 'AI-by-member'

        query_params = (ElasticsearchQueryBuilder()
                        .add_filter('term', {'data.names.normalized_name': name_label})
                        .add_filter('term', {'data.public': True})
                        .add_rank_feature('metadata.members_count')
                        .add_rank_feature('template.members_system_interesting_score_median')
                        .add_rank_feature('template.valid_members_ratio')
                        .add_rank_feature('template.nonavailable_members_ratio', boost=10)
                        .set_source(False)
                        .set_sort_order(sort_order=sort_order, field='data.collection_name.raw')
                        .include_fields(fields)
                        .add_limit(max_results)
                        .add_offset(offset)
                        .build_params())
        try:
            collections, es_response_metadata = self._execute_query(query_params, limit_names)
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [by-member]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        return collections, es_response_metadata

    def get_collections_by_id_list(self, id_list: list[str]) -> list[Collection]:

        fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank', 'metadata.owner',
            'metadata.members_count', 'template.top10_names.normalized_name', 'template.top10_names.namehash',
            'template.collection_types', 'metadata.modified', 'data.avatar_emoji', 'data.avatar_image'
        ]

        try:
            query_params = (ElasticsearchQueryBuilder()
                            .set_terms('metadata.id.keyword', id_list)
                            .include_fields(fields)
                            .add_limit(len(id_list))
                            .build_params())

            collections, _ = self._execute_query(query_params, limit_names=10)
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [by-id_list]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        return collections
