from typing import Optional
import logging

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

        include_fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.collection_types', 'metadata.modified'
        ]

        query_fields = [
            'data.collection_name^3', 'data.collection_name.exact^3', 'data.collection_description',
            'data.collection_keywords^2', 'data.names.normalized_name', 'data.names.tokenized_name'
        ]

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None
        query_params = ElasticsearchQueryBuilder() \
            .add_query(tokenized_query, fields=query_fields, type_='most_fields') \
            .add_limit(max_related_collections if not apply_diversity else max_related_collections * 3) \
            .set_source({'includes': ['data.names.tokenized_name']}) \
            .include_fields(include_fields) \
            .add_rank_feature('template.collection_rank', boost=100) \
            .add_rank_feature('metadata.members_rank_mean', boost=1) \
            .add_rank_feature('metadata.members_rank_median', boost=1) \
            .add_rank_feature('template.members_system_interesting_score_mean', boost=1) \
            .add_rank_feature('template.members_system_interesting_score_median', boost=1) \
            .add_rank_feature('template.valid_members_count', boost=1) \
            .add_rank_feature('template.invalid_members_count', boost=1) \
            .add_rank_feature('template.valid_members_ratio', boost=1) \
            .add_rank_feature('template.nonavailable_members_count', boost=1) \
            .add_rank_feature('template.nonavailable_members_ratio', boost=1) \
            .rescore_with_learning_to_rank(tokenized_query,
                                           window_size=self.ltr_window_size.instant,
                                           model_name=self.ltr_model_name,
                                           feature_set=self.ltr_feature_set,
                                           feature_store=self.ltr_feature_store,
                                           query_weight=0.001,
                                           rescore_query_weight=1000) \
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
            raise ex
