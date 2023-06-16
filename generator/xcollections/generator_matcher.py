from typing import Optional
import logging

from generator.xcollections.matcher import CollectionMatcher
from generator.xcollections.collection import Collection

logger = logging.getLogger('generator')


class CollectionMatcherForGenerator(CollectionMatcher):
    def search_for_generator(
            self,
            tokens: tuple[str, ...],
            max_related_collections: int = 5,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: Optional[int] = 10,
    ) -> tuple[list[Collection], dict]:

        if not self.active:
            return [], {}

        tokenized_query = ' '.join(tokens)

        try:
            return self._search_related(
                query=tokenized_query,
                max_limit=max_related_collections,
                name_diversity_ratio=name_diversity_ratio,
                max_per_type=max_per_type,
                limit_names=limit_names,
                include_tokens=True,
            )
        except Exception as ex:
            logger.warning(f'Elasticsearch search failed', exc_info=True)
            return [], {}
