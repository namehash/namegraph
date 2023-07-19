import gc
import logging, random, hashlib, json
from typing import List, Optional
from operator import attrgetter
from time import perf_counter

import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from hydra import initialize, compose
from pydantic_settings import BaseSettings

from generator.generated_name import GeneratedName
from generator.utils.log import LogEntry
from generator.xgenerator import Generator
from generator.xcollections import CollectionMatcherForAPI, OtherCollectionsSampler
from generator.xcollections.collection import Collection
from generator.domains import Domains
from generator.generation.categories_generator import Categories
from generator.normalization.namehash_normalizer import NamehashNormalizer

logger = logging.getLogger('generator')


# gc.set_debug(gc.DEBUG_STATS)

class Settings(BaseSettings):
    # config_name: str = "test_config"
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
other_collections_sampler = OtherCollectionsSampler(generator.config)
labelhash_normalizer = NamehashNormalizer(generator.config)

domains = Domains(generator.config)
categories = Categories(generator.config)

from models import (
    Name,
    Suggestion,
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


def convert_to_suggestion_format(names: List[GeneratedName], include_metadata: bool = True) -> list[dict[str, str]]:
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
                'collection_id': name.collection_id
            }

    return response


@app.post("/", response_model=list[Suggestion])
async def root(name: Name):
    seed_all(name.name)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.name}')
    params = name.params.model_dump() if name.params is not None else dict()

    generator.clear_cache()
    result = generator.generate_names(name.name,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_suggestion_format(result, include_metadata=name.metadata)

    logger.info(json.dumps(log_entry.create_log_entry(name.model_dump(), result)))

    return JSONResponse(response)


def convert_to_grouped_suggestions_format(names: List[GeneratedName], include_metadata: bool = True):
    response = convert_to_suggestion_format(names, include_metadata=include_metadata)

    # todo: group suggestions based on pipeline_name, collection_title and name


@app.post("/grouped_by_category", response_model=list[Suggestion])
async def root(name: Name):
    seed_all(name.name)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.name}')
    params = name.params.dict() if name.params is not None else dict()
    params['mode'] = 'grouped'

    generator.clear_cache()
    result = generator.generate_names(name.name,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_suggestion_format(result, include_metadata=name.metadata)

    logger.info(json.dumps(log_entry.create_log_entry(name.dict(), result)))

    return JSONResponse(response)


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

    return JSONResponse(response)


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

    return JSONResponse({'count': count, 'metadata': metadata})


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

    return JSONResponse(response)


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

    return JSONResponse({'count': count, 'metadata': metadata})


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

    return JSONResponse({'collections': collections, 'metadata': metadata})
