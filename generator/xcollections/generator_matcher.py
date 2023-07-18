from typing import Optional
import logging

from fastapi import HTTPException

from generator.xcollections.matcher import CollectionMatcher
from generator.xcollections.collection import Collection
from generator.xcollections.query_builder import ElasticsearchQueryBuilder

logger = logging.getLogger('generator')


class CollectionMatcherForGenerator(CollectionMatcher):
    def search_for_generator(
            self,
            tokens: tuple[str, ...],
            max_related_collections: int = 5,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: int = 10,
    ) -> tuple[list[Collection], dict]:

        if not self.active:
            return [], {}

        tokenized_query = ' '.join(tokens)

        fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.collection_types', 'metadata.modified'
        ]

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None
        query_params = ElasticsearchQueryBuilder() \
            .add_query(tokenized_query) \
            .add_limit(max_related_collections if not apply_diversity else max_related_collections * 3) \
            .add_rank_feature('template.collection_rank', boost=100) \
            .add_rank_feature('metadata.members_count') \
            .include_fields(fields) \
            .set_source({'includes': ['data.names.tokenized_name']}) \
            .build_params()

        try:
            collections, es_response_metadata = self._execute_query(query_params, limit_names)

            if not apply_diversity:
                return collections[:max_related_collections], es_response_metadata

            diversified = self._apply_diversity(
                collections,
                max_related_collections,
                name_diversity_ratio,
                max_per_type
            )
            return diversified, es_response_metadata
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [collections generator]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex
