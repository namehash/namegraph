from typing import Optional
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
            'template.top10_names.namehash', 'template.collection_types'
        ]

        try:
            return self._search_related(
                query=query,
                max_limit=max_related_collections,
                fields=fields,
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

    def get_collections_membership_count_for_name(self, normalized_name: str) -> int:
        query_body = ElasticsearchQueryBuilder() \
            .add_filter('term', {'data.names.normalized_name': normalized_name}) \
            .add_filter('term', {'data.public': True}) \
            .build()

        response = self.elastic.count(
            index=self.index_name,
            body=query_body
        )

        return response['count']
