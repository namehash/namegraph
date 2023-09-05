import gc
import logging, random, hashlib, json
from typing import List, Optional
from collections import defaultdict
from time import perf_counter

import numpy as np
from fastapi import FastAPI
from fastapi.responses import Response
from hydra import initialize, compose
from pydantic_settings import BaseSettings

from generator.generated_name import GeneratedName
from generator.utils.log import LogEntry
from generator.xgenerator import Generator
from generator.xcollections import CollectionMatcherForAPI, OtherCollectionsSampler, CollectionMatcherForGenerator
from generator.xcollections.collection import Collection
from generator.domains import Domains
from generator.generation.categories_generator import Categories
from generator.normalization.namehash_normalizer import NamehashNormalizer

logger = logging.getLogger('generator')


# gc.set_debug(gc.DEBUG_STATS)

class Settings(BaseSettings):
    config_name: str = "prod_config_new"
    config_overrides: Optional[list[str]] = None

    # elasticsearch_host: Optional[str] = None
    # elasticsearch_port: Optional[int] = None
    # elasticsearch_username: Optional[str] = None
    # elasticsearch_password: Optional[str] = None
    # elasticsearch_index: Optional[str] = None


settings = Settings()
app = FastAPI()


def init():
    with initialize(version_base=None, config_path="conf/"):
        overrides = settings.config_overrides if settings.config_overrides is not None else []
        config = compose(config_name=settings.config_name, overrides=overrides)
        logger.setLevel(config.app.logging_level)
        for handler in logger.handlers:
            handler.setLevel(config.app.logging_level)

        # overriding elasticsearch data with environment variables
        # if settings.elasticsearch_host:
        #     config.elasticsearch.host = settings.elasticsearch_host
        # if settings.elasticsearch_port:
        #     config.elasticsearch.port = settings.elasticsearch_port
        # if settings.elasticsearch_username:
        #     config.elasticsearch.username = settings.elasticsearch_username
        # if settings.elasticsearch_password:
        #     config.elasticsearch.password = settings.elasticsearch_password
        # if settings.elasticsearch_index:
        #     config.elasticsearch.index = settings.elasticsearch_index

        generator = Generator(config)
        generator.generate_names('cat', min_suggestions=100, max_suggestions=100, min_available_fraction=0.9)  # init
        return generator


def init_inspector():
    with initialize(version_base=None, config_path="conf/"):
        config = compose(config_name=settings.config_name)
        logger.setLevel(config.app.logging_level)
        for handler in logger.handlers:
            handler.setLevel(config.app.logging_level)

        # return Inspector(config)


def seed_all(seed: int | str):
    if isinstance(seed, str):
        hashed = hashlib.md5(seed.encode('utf-8')).digest()
        seed = int.from_bytes(hashed, 'big') & 0xff_ff_ff_ff

    logger.info(f'Setting all seeds to {seed}')
    random.seed(seed)
    np.random.seed(seed)


generator = init()
inspector = init_inspector()

# TODO move this elsewhere, temporary for now
collections_matcher = CollectionMatcherForAPI(generator.config)
generator_matcher = CollectionMatcherForGenerator(generator.config)
other_collections_sampler = OtherCollectionsSampler(generator.config)
labelhash_normalizer = NamehashNormalizer(generator.config)

domains = Domains(generator.config)
categories = Categories(generator.config)

from models import (
    NameRequest,
    Suggestion,
    SampleCollectionMembers,
    GroupedSuggestions,
    Top10CollectionMembersRequest, GroupedNameRequest,
)

from collection_models import (
    CollectionSearchResponse,
    CollectionSearchByCollection,
    CollectionSearchByString,
    CollectionsContainingNameCountResponse,
    CollectionsContainingNameCountRequest,
    CollectionsContainingNameRequest,
    CollectionsContainingNameResponse,
    CollectionCountByStringRequest,
)


def convert_to_suggestion_format(
        names: List[GeneratedName],
        include_metadata: bool = True
) -> list[dict[str, str | dict]]:

    response = [{
        'name': str(name) + '.eth',
        # TODO this should be done using Domains (with or without duplicates if multiple suffixes available for one label?)
    } for name in names]

    if include_metadata:
        for name, name_json in zip(names, response):
            name_json['metadata'] = {
                'applied_strategies': name.applied_strategies,
                'cached_interesting_score': domains.get_interesting_score(name),
                'cached_status': name.status,
                'categories': categories.get_categories(str(name)),
                'interpretation': name.interpretation,
                'pipeline_name': name.pipeline_name,
                'collection_title': name.collection_title,
                'collection_id': name.collection_id,
                'collection_members_count': name.collection_members_count,
                'grouping_category': name.grouping_category
            }

    return response


@app.post("/", response_model=list[Suggestion])
async def root(name: NameRequest):
    seed_all(name.label)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.label}')
    params = name.params.model_dump() if name.params is not None else dict()

    generator.clear_cache()
    result = generator.generate_names(name.label,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_suggestion_format(result, include_metadata=name.metadata)
    logger.info(json.dumps(log_entry.create_log_entry(name.model_dump(), result)))

    return response


def convert_to_grouped_suggestions_format(
        names: List[GeneratedName],
        include_metadata: bool = True
) -> dict[ str, list[dict]]:

    ungrouped_response = convert_to_suggestion_format(names, include_metadata=True)
    grouped_dict: dict[str, list] = {
        c: [] for c in ['wordplay', 'alternates', 'emojify', 'community', 'expand', 'gowild']}
    category_fancy_names = {
        'wordplay': 'Word Play',
        'alternates': 'Alternates',
        'emojify': '😍 Emojify',
        'community': 'Community',
        'expand': 'Expand',
        'gowild': 'Go Wild'
    }
    related_dict: dict[tuple[str, str, int], list] = defaultdict(list)
    collection_categories_order = []

    for suggestion in ungrouped_response:
        grouping_category_type = suggestion['metadata']['grouping_category']

        if grouping_category_type == 'related':
            collection_key = (
                suggestion['metadata']['collection_title'],
                suggestion['metadata']['collection_id'],
                suggestion['metadata']['collection_members_count'],
            )
            related_dict[collection_key].append(suggestion)

            if collection_key not in collection_categories_order:
                collection_categories_order.append(collection_key)
        elif grouping_category_type not in grouped_dict.keys():
            raise ValueError(f'Unexpected grouping_category: {grouping_category_type}')
        else:
            grouped_dict[grouping_category_type].append(suggestion)

    grouped_response: list[dict] = []

    for gcat in generator.config.generation.grouping_categories_order:
        if gcat == 'related' and related_dict.keys():
            for collection_key in collection_categories_order:
                grouped_response.append({
                    'suggestions': related_dict[collection_key] if include_metadata else
                    [{'name': s['name']} for s in related_dict[collection_key]],
                    'type': 'related',
                    'name': collection_key[0],
                    'collection_title': collection_key[0],
                    'collection_id': collection_key[1],
                    'collection_members_count': collection_key[2],
                })
        elif grouped_dict[gcat]:
            grouped_response.append({
                'suggestions': grouped_dict[gcat] if include_metadata else
                [{'name': s['name']} for s in grouped_dict[gcat]],
                'type': gcat,
                'name': category_fancy_names[gcat],
            })

    response = {'categories': grouped_response}
    return response


@app.post("/grouped_by_category_old", response_model=GroupedSuggestions)
async def root(name: NameRequest):
    seed_all(name.label)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.label}')
    params = name.params.model_dump() if name.params is not None else dict()
    params['mode'] = 'grouped_' + params['mode']

    generator.clear_cache()
    result = generator.generate_names(name.label,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_grouped_suggestions_format(result, include_metadata=name.metadata)
    logger.info(json.dumps(log_entry.create_log_entry(name.model_dump(), result)))

    return response

@app.post("/grouped_by_category", response_model=GroupedSuggestions)
async def root(name: GroupedNameRequest):
    seed_all(name.label)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.label}')
    params = name.params.model_dump() if name.params is not None else dict()
    params['mode'] = 'grouped_' + params['mode']

    generator.clear_cache()
    result = generator.generate_names(name.label,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_grouped_suggestions_format(result, include_metadata=name.metadata)
    logger.info(json.dumps(log_entry.create_log_entry(name.model_dump(), result)))

    return response

@app.post("/sample_collection_members", response_model=list[Suggestion])
async def sample_collection_members(sample_command: SampleCollectionMembers):
    result,  es_response_metadata = generator_matcher.sample_members_from_collection(
        sample_command.collection_id,
        sample_command.seed,
        sample_command.max_sample_size
    )

    sampled_members = []
    for name in result['sampled_members']:
        obj = GeneratedName(tokens=(name,),
                            pipeline_name='sample_collection_members',
                            collection_id=result['collection_id'],
                            collection_title=result['collection_title'],
                            grouping_category='related',
                            applied_strategies=[])
        obj.interpretation = []
        sampled_members.append(obj)

    response = convert_to_suggestion_format(sampled_members, include_metadata=sample_command.metadata)

    return response


@app.post("/fetch_top_collection_members", response_model=list[Suggestion])
async def fetch_top_collection_members(fetch_top10_command: Top10CollectionMembersRequest):
    """
    * this endpoint returns top 10 members from the collection specified by collection_id
    """
    result,  es_response_metadata = generator_matcher.fetch_top10_members_from_collection(
        fetch_top10_command.collection_id
    )

    top_members = []
    for name in result['top_members']:
        obj = GeneratedName(tokens=(name,),
                            pipeline_name='fetch_top_collection_members',
                            collection_id=result['collection_id'],
                            collection_title=result['collection_title'],
                            grouping_category='related',
                            applied_strategies=[])
        obj.interpretation = []
        top_members.append(obj)

    response = convert_to_suggestion_format(top_members, include_metadata=fetch_top10_command.metadata)

    return response


def convert_to_collection_format(collections: list[Collection]):
    collections_json = [
        {
            'collection_id': collection.collection_id,
            'title': collection.title,
            'owner': collection.owner,
            'number_of_names': collection.number_of_names,
            'last_updated_timestamp': collection.modified_timestamp,
            'top_names': [{
                'name': name + '.eth',
                'namehash': namehash,
            } for name, namehash in zip(collection.names, collection.namehashes)],
            'types': collection.name_types,
            'avatar_emoji': collection.avatar_emoji,
            'avatar_image': collection.avatar_image
        }
        for collection in collections
    ]
    return collections_json


@app.post("/find_collections_by_string", response_model=CollectionSearchResponse)
async def find_collections_by_string(query: CollectionSearchByString):
    t_before = perf_counter()

    if not collections_matcher.active:
        return Response(status_code=503, content='Elasticsearch Unavailable')

    if not labelhash_normalizer.normalize(query.query):
        related_collections = []
        es_search_metadata = {'n_total_hits': 0}
    else:
        related_collections, es_search_metadata = collections_matcher.search_by_string(
            query.query,
            mode=query.mode,
            max_related_collections=query.max_related_collections,
            offset=query.offset,
            sort_order=query.sort_order,
            name_diversity_ratio=query.name_diversity_ratio,
            max_per_type=query.max_per_type,
            limit_names=query.limit_names,
        )
        related_collections = convert_to_collection_format(related_collections)

    other_collections = other_collections_sampler.get_other_collections(
        n_primary_collections=len(related_collections),
        min_other_collections=query.min_other_collections,
        max_other_collections=query.max_other_collections,
        max_total_collections=query.max_total_collections
    )
    other_collections = convert_to_collection_format(other_collections)

    time_elapsed = (perf_counter() - t_before) * 1000

    metadata = {
        'total_number_of_matched_collections': es_search_metadata.get('n_total_hits', None),
        'processing_time_ms': time_elapsed,
        'elasticsearch_processing_time_ms': es_search_metadata.get('took', None),
        'elasticsearch_communication_time_ms': es_search_metadata.get('elasticsearch_communication_time', None),
    }

    response = {
        'related_collections': related_collections,
        'other_collections': other_collections,
        'metadata': metadata
    }

    return response


@app.post("/count_collections_by_string", response_model=CollectionsContainingNameCountResponse)
async def get_collections_count_by_string(query: CollectionCountByStringRequest):
    t_before = perf_counter()

    if not collections_matcher.active:
        return Response(status_code=503, content='Elasticsearch Unavailable')

    if not labelhash_normalizer.normalize(query.query):
        count = 0
        es_response_metadata = {'n_total_hits': 0}
    else:
        count, es_response_metadata = collections_matcher.get_collections_count_by_string(query.query,
                                                                                          mode=query.mode)

    time_elapsed = (perf_counter() - t_before) * 1000

    metadata = {
        'total_number_of_matched_collections': es_response_metadata.get('n_total_hits', None),
        'processing_time_ms': time_elapsed,
        'elasticsearch_processing_time_ms': es_response_metadata.get('took', None),
        'elasticsearch_communication_time_ms': es_response_metadata.get('elasticsearch_communication_time', None),
    }

    return {'count': count, 'metadata': metadata}


@app.post("/find_collections_by_collection", response_model=CollectionSearchResponse)
async def find_collections_by_collection(query: CollectionSearchByCollection):
    """
    * this search raises exception with status code 404 if the collection with id `collection_id` is absent
    """
    t_before = perf_counter()

    if not collections_matcher.active:
        return Response(status_code=503, content='Elasticsearch Unavailable')

    related_collections, es_search_metadata = collections_matcher.search_by_collection(
        query.collection_id,
        max_related_collections=query.max_related_collections,
        name_diversity_ratio=query.name_diversity_ratio,
        max_per_type=query.max_per_type,
        limit_names=query.limit_names,
        sort_order=query.sort_order,
        offset=query.offset
    )
    related_collections = convert_to_collection_format(related_collections)

    other_collections = other_collections_sampler.get_other_collections(
        n_primary_collections=len(related_collections),
        min_other_collections=query.min_other_collections,
        max_other_collections=query.max_other_collections,
        max_total_collections=query.max_total_collections
    )
    other_collections = convert_to_collection_format(other_collections)

    time_elapsed = (perf_counter() - t_before) * 1000

    metadata = {
        'total_number_of_matched_collections': es_search_metadata.get('n_total_hits', None),
        'processing_time_ms': time_elapsed,
        'elasticsearch_processing_time_ms': es_search_metadata.get('took', None),
        'elasticsearch_communication_time_ms': es_search_metadata.get('elasticsearch_communication_time', None),
    }

    response = {
        'related_collections': related_collections,
        'other_collections': other_collections,
        'metadata': metadata
    }

    return response


@app.post("/count_collections_by_member", response_model=CollectionsContainingNameCountResponse)
async def get_collections_membership_count(request: CollectionsContainingNameCountRequest):
    t_before = perf_counter()

    if not collections_matcher.active:
        return Response(status_code=503, content='Elasticsearch Unavailable')

    if not labelhash_normalizer.normalize(request.label):
        count = 0
        es_response_metadata = {'n_total_hits': 0}
    else:
        count, es_response_metadata = collections_matcher.get_collections_membership_count_for_name(request.label)

    time_elapsed = (perf_counter() - t_before) * 1000

    metadata = {
        'total_number_of_matched_collections': None,
        'processing_time_ms': time_elapsed,
        'elasticsearch_processing_time_ms': es_response_metadata.get('took', None),
        'elasticsearch_communication_time_ms': es_response_metadata.get('elasticsearch_communication_time', None),
    }

    return {'count': count, 'metadata': metadata}


@app.post("/find_collections_by_member", response_model=CollectionsContainingNameResponse)
async def find_collections_membership_list(request: CollectionsContainingNameRequest):
    t_before = perf_counter()

    if not collections_matcher.active:
        return Response(status_code=503, content='Elasticsearch Unavailable')

    if not labelhash_normalizer.normalize(request.label):
        collections_featuring_label = []
        es_search_metadata = {'n_total_hits': 0}
    else:
        collections_featuring_label, es_search_metadata = collections_matcher.get_collections_membership_list_for_name(
            request.label,
            limit_names=request.limit_names,
            sort_order=request.sort_order,
            max_results=request.max_results,
            offset=request.offset,
        )

    collections = convert_to_collection_format(collections_featuring_label)

    time_elapsed = (perf_counter() - t_before) * 1000

    metadata = {
        'total_number_of_matched_collections': es_search_metadata.get('n_total_hits', None),
        'processing_time_ms': time_elapsed,
        'elasticsearch_processing_time_ms': es_search_metadata.get('took', None),
        'elasticsearch_communication_time_ms': es_search_metadata.get('elasticsearch_communication_time', None),
    }

    return {'collections': collections, 'metadata': metadata}
