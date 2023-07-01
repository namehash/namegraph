import json
import random
from omegaconf import DictConfig

from generator.utils import Singleton
from .collection import Collection
from .api_matcher import CollectionMatcherForAPI


class OtherCollectionsSampler(metaclass=Singleton):
    def __init__(self, config: DictConfig):
        self.config = config
        self.other_collections_path = config.collections.other_collections_path
        self.api_matcher = CollectionMatcherForAPI(config)
        with open(self.other_collections_path, 'r', encoding='utf-8') as f:
            other_collections_records: list[dict[str, str]] = json.load(f)
        self.other_collections: list[Collection] = self._retrieve_full_collections_from_es(other_collections_records)

    def _sample_collections(self, k: int) -> list[Collection]:
        return random.sample(self.other_collections, k=k)

    def _retrieve_full_collections_from_es(self, collection_records: list[dict[str, str]]) -> list[Collection]:
        collection_ids = [c['id'] for c in collection_records]
        return self.api_matcher.get_collections_by_id_list(collection_ids)

    def get_other_collections(
            self,
            n_primary_collections: int,
            min_other_collections: int,
            max_other_collections: int,
            max_total_collections: int
    ) -> list[Collection]:
        to_sample = max_total_collections - n_primary_collections
        if to_sample < min_other_collections:
            pass  # not possible because of validation (min_other_c <= max_total_c - max_related_c)
        elif to_sample > max_other_collections:
            to_sample = max_other_collections
        return self._sample_collections(k=to_sample)
