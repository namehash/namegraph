import gc
import logging, random, hashlib, json
from typing import List, Optional
from time import perf_counter

import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from hydra import initialize, compose
from pydantic import BaseSettings

from generator.generated_name import GeneratedName
from generator.utils.log import LogEntry
from generator.xgenerator import Generator
from generator.collection import CollectionMatcher
from generator.domains import Domains
from generator.generation.categories_generator import Categories

logger = logging.getLogger('generator')

# gc.set_debug(gc.DEBUG_STATS)

class Settings(BaseSettings):
    # config_name: str = "test_config"
    config_name: str = "prod_config_new"
    config_overrides: Optional[str] = None

    # elasticsearch_host: Optional[str] = None
    # elasticsearch_port: Optional[int] = None
    # elasticsearch_username: Optional[str] = None
    # elasticsearch_password: Optional[str] = None
    # elasticsearch_index: Optional[str] = None


settings = Settings()
app = FastAPI()


def init():
    with initialize(version_base=None, config_path="conf/"):
        overrides = json.loads(settings.config_overrides) if settings.config_overrides is not None else []
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

domains = Domains(generator.config)
categories = Categories(generator.config)

from models import (
    Name,
    Suggestion,
    CollectionSearchResponse,
    CollectionSearchByCollection,
    CollectionSearchByString,
    CollectionsFeaturingNameCountResponse,
    CollectionsFeaturingNameCountRequest,
    CollectionsFeaturingNameRequest,
    CollectionsFeaturingNameResponse
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
                'collection': name.collection
            }

    return response


@app.post("/", response_model=list[Suggestion])
async def root(name: Name):
    seed_all(name.name)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.name}')
    params = name.params.dict() if name.params is not None else dict()

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


# ========================= Collections API =========================

collections_matcher = CollectionMatcher(generator.config)


@app.post("/find_collections_by_string", response_model=CollectionSearchResponse)
async def find_collections_by_string(query: CollectionSearchByString):
    t_before = perf_counter()

    collections, es_search_metadata = collections_matcher.search_by_string(
        query.query,
        mode=query.mode,
        max_related_collections=query.max_related_collections,
        min_other_collections=query.min_other_collections,
        max_other_collections=query.max_other_collections,
        max_total_collections=query.max_total_collections,
        name_diversity_ratio=query.name_diversity_ratio,
        max_per_type=query.max_per_type,
        limit_names=query.limit_names,
    )

    time_elapsed = (perf_counter() - t_before) * 1000
  
    metadata = {
        'total_number_of_matched_collections': es_search_metadata.get('n_total_hits', None),
        'processing_time_ms': time_elapsed
    }

    response = {'related_collections': collections, 'other_collections': [], 'metadata': metadata}


    return JSONResponse(response)


@app.post("/find_collections_by_collection", response_model=CollectionSearchResponse)
async def find_collections_by_collection(query: CollectionSearchByCollection):
    t_before = perf_counter()

    collections, es_search_metadata  = collections_matcher.search_by_collection(
        query.collection_id,
        max_related_collections=query.max_related_collections,
        min_other_collections=query.min_other_collections,
        max_other_collections=query.max_other_collections,
        max_total_collections=query.max_total_collections,
        name_diversity_ratio=query.name_diversity_ratio,
        max_per_type=query.max_per_type,
        limit_names=query.limit_names,
    )
    
    time_elapsed = (perf_counter() - t_before) * 1000
  
    metadata = {
        'total_number_of_matched_collections': es_search_metadata.get('n_total_hits', None),
        'processing_time_ms': time_elapsed
    }

    response = {'related_collections': collections, 'other_collections': [], 'metadata': metadata}

    return JSONResponse(response)


@app.post("/get_collections_featuring_name_count", response_model=CollectionsFeaturingNameCountResponse)
async def get_collections_membership_count(request: CollectionsFeaturingNameCountRequest):
    t_before = perf_counter()

    count = collections_matcher.get_collections_membership_count_for_name(request.label)

    time_elapsed = (perf_counter() - t_before) * 1000

    metadata = {
        'processing_time_ms': time_elapsed
    }

    return JSONResponse({'count': count, 'metadata': metadata})


@app.post("/find_collections_featuring_name", response_model=CollectionsFeaturingNameResponse)
async def find_collections_membership_list(request: CollectionsFeaturingNameRequest):
    t_before = perf_counter()

    sort_order = request.sort_order
    collections_featuring_label, es_search_metadata = collections_matcher.get_collections_membership_list_for_name(
        request.label,
        n_top_names=request.limit_names
    )

    # todo: move sort to ES query
    if sort_order == 'A-Z':
        collections_featuring_label.sort(key=lambda x: x['title'])
    elif sort_order == 'Z-A':
        collections_featuring_label.sort(key=lambda x: x['title'], reverse=True)
    elif sort_order == 'AI':
        pass
    else:
        logger.warning(f"Unexpected type of sort_order: '{sort_order}'. Using A-Z order.")
        collections_featuring_label.sort(key=lambda x: x['title'])

    time_elapsed = (perf_counter() - t_before) * 1000

    metadata = {
        'total_number_of_matched_collections': es_search_metadata.get('n_total_hits', None),
        'processing_time_ms': time_elapsed
    }

    return JSONResponse({'collections': collections_featuring_label, 'metadata': metadata})
