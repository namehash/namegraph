from typing import Optional, Literal, Union
import logging

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

        if not self.active:
            return [], {}

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
            logger.warning(f'Elasticsearch search failed', exc_info=True)
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
            logger.warning(f'Elasticsearch search failed', exc_info=True)
            return [], {}

    def get_collections_membership_count_for_name(self, name_label: str) -> tuple[Union[int,str], dict]:
        query_body = ElasticsearchQueryBuilder() \
            .add_filter('term', {'data.names.normalized_name': name_label}) \
            .add_filter('term', {'data.public': True}) \
            .build()

        response = self.elastic.count(
            index=self.index_name,
            body=query_body
        )
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

        query_body = (ElasticsearchQueryBuilder()
                      .add_filter('term', {'data.names.normalized_name': name_label})
                      .add_filter('term', {'data.public': True})
                      .add_rank_feature('metadata.members_count')
                      .add_rank_feature('template.members_system_interesting_score_median')
                      .add_rank_feature('template.valid_members_ratio')
                      .add_rank_feature('template.nonavailable_members_ratio', boost=10)
                      .set_source(False)
                      .set_sort_order(sort_order=sort_order if sort_order != 'AI' else 'AI-by-member',
                                      field='data.collection_name.raw')
                      .include_fields(fields)
                      .add_limit(max_results)
                      .add_offset(offset)
                      .build())

        collections, es_response_metadata = self._execute_query(query_body, limit_names)

        return collections, es_response_metadata
