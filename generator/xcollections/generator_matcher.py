from typing import Optional
from time import perf_counter
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
            'metadata.id', 'data.collection_name', 'template.collection_rank', 'metadata.owner',
            'metadata.members_count', 'template.top10_names.normalized_name', 'template.top10_names.namehash',
            'template.collection_types', 'metadata.modified', 'data.avatar_emoji', 'data.avatar_image'
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

    def sample_members_from_collection(
            self,
            collection_id: str,
            seed: int,
            max_sample_size: int = 10,
    ) -> tuple[dict, dict]:

        # FIXME do we need this?
        # if not self.active:
        #     return [], {}

        fields = ['metadata.id', 'data.collection_name']

        sampling_script = """
            def number_of_names = params._source.data.names.size();
            def random = new Random(params.seed);

            if (number_of_names <= params.max_sample_size) {
                return params._source.data.names.stream()
                    .map(n -> n.normalized_name)
                    .collect(Collectors.toList())
            }

            if (number_of_names <= 100 || params.max_sample_size * 2 >= number_of_names) {
                Collections.shuffle(params._source.data.names, random);
                return params._source.data.names.stream()
                    .limit(params.max_sample_size)
                    .map(n -> n.normalized_name)
                    .collect(Collectors.toList());
            }

            def set = new HashSet();

            while (set.size() < params.max_sample_size) {
                def index = random.nextInt(number_of_names);
                set.add(index);
            }

            return set.stream().map(i -> params._source.data.names[i].normalized_name).collect(Collectors.toList());
        """

        query_params = ElasticsearchQueryBuilder() \
            .set_term('metadata.id.keyword', collection_id) \
            .include_fields(fields) \
            .set_source(False) \
            .include_script_field(name='sampled_members',
                                  script=sampling_script,
                                  lang='painless',
                                  params={'seed': seed, 'max_sample_size': max_sample_size}) \
            .build_params()

        try:
            t_before = perf_counter()
            response = self.elastic.search(index=self.index_name, **query_params)
            time_elapsed = (perf_counter() - t_before) * 1000
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [collection members sampling]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        try:
            hit = response['hits']['hits'][0]
            es_response_metadata = {
                'n_total_hits': 1,
                'took': response['took'],
                'elasticsearch_communication_time': time_elapsed,
            }
        except IndexError as ex:
            raise HTTPException(status_code=404, detail=f'Collection with id={collection_id} not found') from ex

        result = {
            'collection_id': hit['fields']['metadata.id'][0],
            'collection_title': hit['fields']['data.collection_name'][0],
            'sampled_members': hit['fields']['sampled_members']
        }

        return result, es_response_metadata
