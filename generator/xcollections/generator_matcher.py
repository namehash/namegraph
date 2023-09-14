from typing import Optional, Literal
from time import perf_counter
from itertools import cycle
from copy import copy
import concurrent.futures
import logging
import random

import elasticsearch.exceptions
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
            'data.collection_name', 'template.collection_rank',
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
            .set_source({'includes': ['data.names.tokenized_name', 'name_generator.related_collections']}) \
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
            'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.collection_types', 'metadata.modified',
        ]

        if sort_order == 'AI':
            sort_order = 'AI-by-member'

        query_params = (ElasticsearchQueryBuilder()
                        .add_filter('term', {'data.names.normalized_name': name_label})
                        .add_filter('term', {'data.public': True})
                        .set_source({'includes': ['data.names.tokenized_name', 'name_generator.related_collections']})
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

        fields = ['data.collection_name']

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
            .set_term('_id', collection_id) \
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
            'collection_id': hit['_id'],
            'collection_title': hit['fields']['data.collection_name'][0],
            'sampled_members': hit['fields']['sampled_members']
        }

        return result, es_response_metadata

    def fetch_top10_members_from_collection(
            self,
            collection_id: str,
            max_recursive_related_collections: int
    ) -> tuple[dict, dict]:

        fields = ['data.collection_name', 'template.top10_names.normalized_name',
                  'metadata.members_count', 'name_generator.related_collections']

        try:
            t_before = perf_counter()
            response = self.elastic.get(index=self.index_name, id=collection_id, _source_includes=fields)
            time_elapsed = (perf_counter() - t_before) * 1000
        except elasticsearch.exceptions.NotFoundError as ex:
            raise HTTPException(status_code=404, detail=f'Collection with id={collection_id} not found') from ex
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [fetch top10 collection members]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        es_response_metadata = {
            'n_total_hits': 1,
            'elasticsearch_communication_time': time_elapsed,
        }

        related_collections = [
            {
                'collection_id': c['collection_id'],
                'collection_title': c['collection_name'],
                'collection_members_count': c['members_count'],
            }
            for c in response['_source']['name_generator']['related_collections']
        ]

        result = {
            'collection_id': response['_id'],
            'collection_title': response['_source']['data']['collection_name'],
            'collection_members_count': response['_source']['metadata']['members_count'],
            'top_members': [item['normalized_name'] for item in response['_source']['template']['top10_names']],
            'related_collections': related_collections[:max_recursive_related_collections]
        }

        return result, es_response_metadata

    def scramble_tokens_from_collection(
            self,
            collection_id: str,
            method: Literal['left-right-shuffle', 'left-right-shuffle-with-unigrams', 'full-shuffle'],
            n_top_members: int,
            max_suggestions: int
    ) -> tuple[dict, dict]:

        fields = ['data.collection_name']

        query_params = ElasticsearchQueryBuilder() \
            .set_term('_id', collection_id) \
            .include_fields(fields) \
            .include_script_field('names_with_tokens', script="params['_source'].data.names.stream()"
                                                              f".limit({n_top_members}).collect(Collectors.toList())") \
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

        name_tokens_tuples = [(r['normalized_name'], r['tokenized_name']) for r in hit['fields']['names_with_tokens']]
        token_scramble_suggestions = self._get_suggestions_by_scrambling_tokens(
            name_tokens_tuples, method, n_suggestions=max_suggestions
        )

        result = {
            'collection_id': hit['_id'],
            'collection_title': hit['fields']['data.collection_name'][0],
            'token_scramble_suggestions': token_scramble_suggestions
        }

        return result, es_response_metadata


    def _get_suggestions_by_scrambling_tokens(
            self,
            name_tokens_tuples: list[tuple[str, list[str]]],
            method: Literal['left-right-shuffle', 'left-right-shuffle-with-unigrams', 'full-shuffle'],
            n_suggestions: Optional[int] = None
    ) -> list[str]:

        # collect bigrams (left and right tokens) and unigrams (collection names that could not be tokenized)
        left_tokens = set()
        right_tokens = set()
        unigrams = set()
        for name, tokenized_name in name_tokens_tuples:
            if len(tokenized_name) == 1:
                further_tokenized_name = self.bigram_longest_tokenizer.get_tokenization(name)
                if further_tokenized_name is None or further_tokenized_name == (name, ''):
                    unigrams.add(name)
                else:
                    left_tokens.add(further_tokenized_name[0])
                    right_tokens.add(further_tokenized_name[1])
            elif len(tokenized_name) == 2:
                left_tokens.add(tokenized_name[0])
                right_tokens.add(tokenized_name[1])
            elif len(tokenized_name) > 2:
                left_tokens.add(tokenized_name[0])
                # todo: there might be a better approach (if more than 2 tokens, cut in the center?)
                right_tokens.add(''.join(tokenized_name[1:]))

        original_names = {t[0] for t in name_tokens_tuples}
        suggestions = []

        left_tokens_list = list(left_tokens)
        right_tokens_list = list(right_tokens)
        unigrams_list = list(unigrams)

        if method == 'left-right-shuffle' or method == 'left-right-shuffle-with-unigrams':
            if method == 'left-right-shuffle-with-unigrams':
                random.shuffle(unigrams_list)
                mid = len(unigrams_list) // 2
                left_tokens_list = list(left_tokens | set(unigrams_list[:mid]))
                right_tokens_list = list(right_tokens | set(unigrams_list[mid:]))
            random.shuffle(left_tokens_list)
            random.shuffle(right_tokens_list)

            # if not enough left/right tokens, repeat tokens
            if n_suggestions is None:
                pass
            elif (est_n_suggestions := min(len(left_tokens_list), len(right_tokens_list))) < n_suggestions:
                n_repeats = min(n_suggestions // est_n_suggestions + 2, est_n_suggestions)
                left_tokens_list *= n_repeats
                right_tokens_list *= n_repeats

            while left_tokens_list and (n_suggestions is None or len(suggestions) < n_suggestions):
                left = left_tokens_list.pop()
                for i, right in enumerate(right_tokens_list):
                    s = left + right
                    if s not in original_names and s not in suggestions:
                        suggestions.append(s)
                        del right_tokens_list[i]
                        break
        elif method == 'full-shuffle':
            all_unigrams = list(left_tokens | right_tokens | unigrams)
            random.shuffle(all_unigrams)

            # if not enough all_unigrams, repeat tokens
            if n_suggestions is None:
                pass
            elif (est_n_suggestions := len(all_unigrams) // 2) < n_suggestions:
                n_repeats = min(n_suggestions // est_n_suggestions + 2, est_n_suggestions)
                all_unigrams *= n_repeats

            while len(all_unigrams) >= 2 and (n_suggestions is None or len(suggestions) < n_suggestions):
                left = all_unigrams.pop()
                for i, right in enumerate(all_unigrams):
                    s = left + right
                    if s not in original_names and s not in suggestions:
                        suggestions.append(s)
                        del all_unigrams[i]
                        break
        else:
            raise ValueError(f'[get_suggestions_by_scrambling_tokens] no such method allowed: \'{method}\'')

        random.shuffle(suggestions)

        if n_suggestions is not None and len(suggestions) != n_suggestions:
            logger.warning(f'[get_suggestions_by_scrambling_tokens] number of suggestions ({len(suggestions)}) '
                           f'does not equal desired n_suggestions ({n_suggestions})')

        return suggestions
