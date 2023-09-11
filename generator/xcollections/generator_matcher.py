from typing import Optional, Literal
from time import perf_counter
from itertools import cycle
import concurrent.futures
import logging

from fastapi import HTTPException

from generator.xcollections.matcher import CollectionMatcher
from generator.xcollections.collection import Collection
from generator.xcollections.query_builder import ElasticsearchQueryBuilder

logger = logging.getLogger('generator')


class CollectionMatcherForGenerator(CollectionMatcher):
    def _search_for_generator(
            self,
            tokens: tuple[str, ...],
            max_related_collections: int = 5,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: int = 10,
            enable_learning_to_rank: bool = True,
    ) -> tuple[list[Collection], dict]:

        if not self.active:
            return [], {}

        tokenized_query = ' '.join(tokens)
        if len(tokens) > 1:
            tokenized_query = ''.join(tokens) + ' ' + tokenized_query

        include_fields = [
            'metadata.id', 'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.collection_types', 'metadata.modified',
        ]

        query_fields = [
            'data.collection_name^3', 'data.collection_name.exact^3', 'data.collection_description',
            'data.collection_keywords^2', 'data.names.normalized_name', 'data.names.tokenized_name'
        ]

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None
        query_builder = ElasticsearchQueryBuilder() \
            .add_limit(max_related_collections if not apply_diversity else max_related_collections * 3) \
            .set_source({'includes': ['data.names.tokenized_name']}) \
            .add_rank_feature('template.collection_rank', boost=100) \
            .include_fields(include_fields)

        if enable_learning_to_rank:
            query_params = query_builder \
                .add_query(tokenized_query, fields=query_fields, type_='most_fields') \
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
        else:
            query_params = query_builder \
                .add_query(tokenized_query, fields=query_fields, type_='cross_fields') \
                .add_rank_feature('metadata.members_count', boost=1) \
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

    # FIXME duplicate of CollectionMatcherForAPI.get_collections_membership_list_for_name
    # FIXME either we remove this or move to a parent class
    def _search_by_membership(
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
            'template.collection_types', 'metadata.modified',
        ]

        if sort_order == 'AI':
            sort_order = 'AI-by-member'

        query_params = (ElasticsearchQueryBuilder()
                        .add_filter('term', {'data.names.normalized_name': name_label})
                        .add_filter('term', {'data.public': True})
                        .set_source({'includes': ['data.names.tokenized_name']})
                        .add_rank_feature('metadata.members_count')
                        .add_rank_feature('template.members_system_interesting_score_median')
                        .add_rank_feature('template.valid_members_ratio')
                        .add_rank_feature('template.nonavailable_members_ratio', boost=10)
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

    def search_for_generator(
            self,
            tokens: tuple[str, ...],
            max_related_collections: int = 5,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: int = 10,
            enable_learning_to_rank: bool = True,
    ) -> tuple[list[Collection], dict]:

        t_before = perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            related_future = executor.submit(
                self._search_for_generator,
                tokens=tokens,
                max_related_collections=max_related_collections,
                name_diversity_ratio=name_diversity_ratio,
                max_per_type=max_per_type,
                limit_names=limit_names,
                enable_learning_to_rank=enable_learning_to_rank
            )

            membership_future = executor.submit(
                self._search_by_membership,
                name_label=''.join(tokens),
                limit_names=limit_names,
                sort_order='AI',
                max_results=max_related_collections,
                offset=0
            )

            related, es_response_metadata1 = related_future.result()
            membership, es_response_metadata2 = membership_future.result()

        time_elapsed = (perf_counter() - t_before) * 1000

        related_iter = iter(related)
        membership_iter = iter(membership)
        common = []
        used_ids = set()
        for iterable, items_to_take in cycle([(related_iter, 2), (membership_iter, 1)]):
            try:
                while items_to_take:
                    item = next(iterable)
                    if item.collection_id not in used_ids:
                        common.append(item)
                        used_ids.add(item.collection_id)
                        items_to_take -= 1
            except StopIteration:
                break

        if len(common) < max_related_collections:
            common.extend(related_iter)
            common.extend(membership_iter)

        if es_response_metadata1['n_total_hits'] == '1000+' or es_response_metadata2['n_total_hits'] == '1000+':
            n_total_hits = '1000+'
        else:
            n_total_hits = es_response_metadata1['n_total_hits'] + es_response_metadata2['n_total_hits']
            n_total_hits = '1000+' if n_total_hits > 1000 else n_total_hits

        es_response_metadata = {
            'n_total_hits': n_total_hits,
            'took': es_response_metadata1['took'] + es_response_metadata2['took'],
            'elasticsearch_communication_time': time_elapsed,
        }

        return common[:max_related_collections], es_response_metadata

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

    def fetch_top10_members_from_collection(self, collection_id: str) -> tuple[dict, dict]:
        fields = ['metadata.id', 'data.collection_name', 'template.top10_names.normalized_name']

        query_params = ElasticsearchQueryBuilder() \
            .set_term('metadata.id.keyword', collection_id) \
            .include_fields(fields) \
            .set_source(False) \
            .build_params()

        try:
            t_before = perf_counter()
            response = self.elastic.search(index=self.index_name, **query_params)
            time_elapsed = (perf_counter() - t_before) * 1000
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [fetch top10 collection members]', exc_info=True)
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
            'top_members': hit['fields']['template.top10_names.normalized_name']
        }

        return result, es_response_metadata


    def scramble_tokens_from_collection(
            self,
            collection_id: str,
            method: str,
            n_top_members: int
    ) -> tuple[dict, dict]:

        # todo: query option with script_names and normal names

        fields = ['metadata.id', 'data.collection_name', 'template.top10_names.normalized_name']

        query_params = ElasticsearchQueryBuilder() \
            .set_term('metadata.id.keyword', collection_id) \
            .include_fields(fields) \
            .set_source(False) \
            .build_params()

        try:
            t_before = perf_counter()
            response = self.elastic.search(index=self.index_name, **query_params)
            time_elapsed = (perf_counter() - t_before) * 1000
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [scramble tokens from collection]', exc_info=True)
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


        # todo: impl. token scramble

        result = {
            'collection_id': hit['fields']['metadata.id'][0],
            'collection_title': hit['fields']['data.collection_name'][0],
            'token_scramble_suggestions': hit['fields']['template.top10_names.normalized_name']  # todo
        }

        return result, es_response_metadata
