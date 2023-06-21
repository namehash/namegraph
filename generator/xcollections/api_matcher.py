from typing import Optional, Literal, Union
import logging
from fastapi import HTTPException

from generator.xcollections.matcher import CollectionMatcher
from generator.xcollections.collection import Collection
from generator.xcollections.query_builder import ElasticsearchQueryBuilder

logger = logging.getLogger('generator')


class CollectionMatcherForAPI(CollectionMatcher):
    def search_by_string(
            self,
            query: str,
            mode: str,
            max_related_collections: int = 3,
            offset: int = 0,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = 'AI',
            min_other_collections: int = 3,
            max_other_collections: int = 3,
            max_total_collections: int = 6,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: int = 10,
    ) -> tuple[list[Collection], dict]:

        tokenized_query = ' '.join(self.tokenizer.tokenize(query)[0])
        if tokenized_query != query:
            query = f'{query} {tokenized_query}'

        fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.top10_names.namehash', 'template.collection_types', 'metadata.modified'
        ]

        try:
            return self._search_related(
                query=query,
                max_limit=max_related_collections,
                fields=fields,
                offset=offset,
                sort_order=sort_order,
                name_diversity_ratio=name_diversity_ratio,
                max_per_type=max_per_type,
                limit_names=limit_names,
            )
        except Exception as ex:
            logger.error(f'Elasticsearch search failed', exc_info=True)
            raise ex

    def search_by_collection(
            self,
            collection_id: str,
            max_related_collections: int = 3,
            min_other_collections: int = 3,
            max_other_collections: int = 3,
            max_total_collections: int = 6,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: Optional[int] = 10,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = 'AI'
    ) -> tuple[list[Collection], dict]:

        if sort_order == 'AI':
            sort_order = 'ES'

        fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.top10_names.namehash', 'template.collection_types', 'metadata.modified'
        ]

        # find collection with specified collection_id
        id_match_body = (ElasticsearchQueryBuilder()
                         .set_term('metadata.id.keyword', collection_id)
                         .set_source(False)
                         .include_fields(fields)
                         .build())

        try:
            collections, es_response_metadata = self._execute_query(id_match_body, limit_names=10)
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [id-to-collection search]', exc_info=True)
            raise ex

        try:
            found_collection = collections[0]
        except IndexError as ex:
            logger.error(f'could not find collection with id {collection_id}', exc_info=True)
            raise HTTPException(status_code=404, detail=f"Collection with id={collection_id} not found.")

        es_time_first = es_response_metadata['took']
        if es_response_metadata['n_total_hits'] > 1:
            logger.warning(f'more than 1 collection found with id {collection_id}')

        # search similar collections
        apply_diversity = name_diversity_ratio is not None or max_per_type is not None

        query_body = (ElasticsearchQueryBuilder()
                      .add_query(found_collection.title, boolean_clause='should', type_='cross_fields',
                                 fields=["data.collection_name^3", "data.collection_name.exact^3", 'data.collection_keywords^2'])
                      .add_query(' '.join(found_collection.names), boolean_clause='should', type_='cross_fields',
                                 fields=["data.names.normalized_name"])
                      .add_filter('term', {'data.public': True})
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
                      .build())
        try:
            collections, es_response_metadata = self._execute_query(query_body, limit_names)
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [collection-to-collections search]', exc_info=True)
            raise ex

        es_response_metadata['took'] += es_time_first

        if not apply_diversity:
            return collections, es_response_metadata

        diversified = self._apply_diversity(collections, max_related_collections, name_diversity_ratio, max_per_type)
        return diversified, es_response_metadata


    def get_collections_membership_count_for_name(self, name_label: str) -> tuple[Union[int, str], dict]:

        query_body = ElasticsearchQueryBuilder() \
            .add_filter('term', {'data.names.normalized_name': name_label}) \
            .add_filter('term', {'data.public': True}) \
            .build()

        try:
            response = self.elastic.count(
                index=self.index_name,
                body=query_body
            )
        except Exception as ex:
            logger.error(f'Elasticsearch count failed', exc_info=True)
            raise ex

        count = response['count']

        return count if count <= 1000 else '1000+', dict()

    def get_collections_membership_list_for_name(
            self,
            name_label: str,
            limit_names: int = 10,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = 'AI',
            max_results: int = 3,
            offset: int = 0
    ) -> tuple[list[Collection], dict]:

        fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.top10_names.namehash', 'template.collection_types', 'metadata.modified'
        ]

        if sort_order == 'AI':
            sort_order = 'AI-by-member'

        query_body = (ElasticsearchQueryBuilder()
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
                      .build())
        try:
            collections, es_response_metadata = self._execute_query(query_body, limit_names)
        except Exception as ex:
            logger.error(f'Elasticsearch count failed', exc_info=True)
            raise ex

        return collections, es_response_metadata
