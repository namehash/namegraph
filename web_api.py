import hashlib
import json
import logging
import random
from collections import defaultdict
from time import perf_counter
from typing import List, Optional

import numpy as np
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from hydra import initialize, compose
from pydantic_settings import BaseSettings

from namegraph.domains import Domains
from namegraph.generated_name import GeneratedName
from namegraph.generation.categories_generator import Categories
from namegraph.normalization.namehash_normalizer import NamehashNormalizer
from namegraph.utils.log import LogEntry
from namegraph.xcollections import CollectionMatcherForAPI, OtherCollectionsSampler, CollectionMatcherForGenerator
from namegraph.xcollections.collection import Collection
from namegraph.xgenerator import Generator, RelatedSuggestions

logger = logging.getLogger('namegraph')


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
app = FastAPI(title="NameGraph API")  # TODO add version

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

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


def seed_all(seed: int | str):
    if isinstance(seed, str):
        hashed = hashlib.md5(seed.encode('utf-8')).digest()
        seed = int.from_bytes(hashed, 'big') & 0xff_ff_ff_ff

    logger.info(f'Setting all seeds to {seed}')
    random.seed(seed)
    np.random.seed(seed)


generator = init()

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
    Top10CollectionMembersRequest,
    GroupedNameRequest,
    ScrambleCollectionTokens,
    CollectionCategory,
    FetchCollectionMembersRequest,
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
    Collection as CollectionModel,
    GetCollectionByIdRequest,
)


def convert_to_suggestion_format(
        names: List[GeneratedName],
        include_metadata: bool = True
) -> list[dict[str, str | dict]]:
    response = [{
        'name': str(name) + '.eth',
        # TODO this should be done using Domains (with or without duplicates if multiple suffixes available for one label?)
        'tokenized_label': list(name.tokens)
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


@app.post("/", response_model=list[Suggestion], tags=['generator'])
async def generate_names(name: NameRequest):
    seed_all(name.label)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.label}')
    params = name.params.model_dump() if name.params is not None else dict()

    result = generator.generate_names(name.label,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_suggestion_format(result, include_metadata=name.metadata)
    logger.info(json.dumps(log_entry.create_log_entry(name.model_dump(), result)))

    return response


category_fancy_names = {
    'wordplay': 'Word Play',
    'alternates': 'Alternates',
    'emojify': '😍 Emojify',
    'community': 'Community',
    'expand': 'Expand',
    'gowild': 'Go Wild',
    'other': 'Other Names'
}


def convert_related_to_grouped_suggestions_format(
        related_suggestions: dict[str, RelatedSuggestions], include_metadata: bool = True) -> list[dict]:
    grouped_response = []
    for collection_key, suggestions in related_suggestions.items():
        converted_suggestions = convert_to_suggestion_format(suggestions, include_metadata=True)
        grouped_response.append({
            'suggestions': converted_suggestions if include_metadata else
            [{k: v for k, v in sug.items() if k != 'metadata'} for sug in converted_suggestions],
            'type': 'related',
            'name': suggestions.collection_title,
            'collection_title': suggestions.collection_title,
            'collection_id': suggestions.collection_id,
            'collection_members_count': suggestions.collection_members_count,
            'related_collections': suggestions.related_collections,
        })
    return grouped_response


def convert_grouped_to_grouped_suggestions_format(
        related_suggestions: dict[str, RelatedSuggestions],
        grouped_suggestions: dict[str, list[GeneratedName]],
        include_metadata: bool = True
) -> dict[str, list[dict]]:
    grouped_response: list[dict] = []
    for gcat in generator.config.generation.grouping_categories_order:
        if gcat == 'related':
            grouped_response.extend(convert_related_to_grouped_suggestions_format(related_suggestions,include_metadata))
        elif gcat in grouped_suggestions:
            converted_suggestions = convert_to_suggestion_format(grouped_suggestions[gcat], include_metadata=True)
            grouped_response.append({
                'suggestions': converted_suggestions if include_metadata else
                [{k: v for k, v in sug.items() if k != 'metadata'} for sug in converted_suggestions],
                'type': gcat,
                'name': category_fancy_names[gcat],
            })

    response = {'categories': grouped_response}
    return response


def convert_to_grouped_suggestions_format(
        names: List[GeneratedName],
        include_metadata: bool = True
) -> dict[str, list[dict]]:
    ungrouped_response = convert_to_suggestion_format(names, include_metadata=True)
    grouped_dict: dict[str, list] = {
        c: [] for c in ['wordplay', 'alternates', 'emojify', 'community', 'expand', 'gowild', 'other']}

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
        if gcat == 'related':
            for collection_key in collection_categories_order:
                grouped_response.append({
                    'suggestions': related_dict[collection_key] if include_metadata else
                    [{k: v for k, v in sug.items() if k != 'metadata'} for sug in related_dict[collection_key]],
                    'type': 'related',
                    'name': collection_key[0],
                    'collection_title': collection_key[0],
                    'collection_id': collection_key[1],
                    'collection_members_count': collection_key[2],
                    'related_collections': [],  # TODO fix if this will be used
                })
        elif grouped_dict[gcat]:
            grouped_response.append({
                'suggestions': grouped_dict[gcat] if include_metadata else
                [{k: v for k, v in sug.items() if k != 'metadata'} for sug in grouped_dict[gcat]],
                'type': gcat,
                'name': category_fancy_names[gcat],
            })

    response = {'categories': grouped_response}
    return response


@app.post("/grouped_by_category", response_model=GroupedSuggestions, tags=['generator'])
async def grouped_by_category(name: NameRequest):
    seed_all(name.label)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.label}')
    params = name.params.model_dump() if name.params is not None else dict()
    params['mode'] = 'grouped_' + params['mode']

    result = generator.generate_names(name.label,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_grouped_suggestions_format(result, include_metadata=name.metadata)
    response['all_tokenizations'] = []  # todo: fix if this will be used

    logger.info(json.dumps(log_entry.create_log_entry(name.model_dump(), result)))

    return response


@app.post("/suggestions_by_category", response_model=GroupedSuggestions, tags=['generator'])
def suggestions_by_category(name: GroupedNameRequest):
    seed_all(name.label)
    log_entry = LogEntry(generator.config)
    logger.debug(f'Request received: {name.label}')
    params = name.params.model_dump() if name.params is not None else dict()
    # params['mode'] = 'grouped_' + params['mode']

    related_suggestions, grouped_suggestions, all_tokenizations  = generator.generate_grouped_names(
        name.label,
        max_related_collections=name.categories.related.max_related_collections,
        max_names_per_related_collection=name.categories.related.max_names_per_related_collection,
        max_recursive_related_collections=name.categories.related.max_recursive_related_collections,
        categories_params=name.categories,
        min_total_suggestions=name.categories.other.min_total_suggestions,
        params=params
    )

    response = convert_grouped_to_grouped_suggestions_format(related_suggestions, grouped_suggestions,
                                                             include_metadata=name.params.metadata)
    response['all_tokenizations'] = all_tokenizations

    logger.info(json.dumps(
        log_entry.create_grouped_log_entry(name.model_dump(), {**related_suggestions, **grouped_suggestions})))

    return response


@app.post("/sample_collection_members", response_model=list[Suggestion], tags=['collections'])
async def sample_collection_members(sample_command: SampleCollectionMembers):
    result, es_response_metadata = generator_matcher.sample_members_from_collection(
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

    logger.info(json.dumps({'endpoint': 'sample_collection_members', 'request': sample_command.model_dump()}))

    return response


@app.post("/fetch_top_collection_members", response_model=CollectionCategory, tags=['collections'])
async def fetch_top_collection_members(fetch_top10_command: Top10CollectionMembersRequest):
    """
    * this endpoint returns top 10 members from the collection specified by collection_id
    """
    result, es_response_metadata = generator_matcher.fetch_top10_members_from_collection(
        fetch_top10_command.collection_id, fetch_top10_command.max_recursive_related_collections
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

    # response = convert_to_suggestion_format(top_members, include_metadata=fetch_top10_command.metadata)

    rs = RelatedSuggestions(result['collection_title'], result['collection_id'], result['collection_members_count'], )
    rs.related_collections = result['related_collections']
    rs.extend(top_members)

    response2 = convert_related_to_grouped_suggestions_format({result['collection_title']: rs},
                                                              include_metadata=fetch_top10_command.metadata)

    logger.info(json.dumps({'endpoint': 'fetch_top_collection_members', 'request': fetch_top10_command.model_dump()}))

    return response2[0]


@app.post("/scramble_collection_tokens", response_model=list[Suggestion], tags=['collections'])
async def scramble_collection_tokens(scramble_command: ScrambleCollectionTokens):
    result, es_response_metadata = generator_matcher.scramble_tokens_from_collection(
        scramble_command.collection_id, scramble_command.method,
        scramble_command.n_top_members, scramble_command.max_suggestions, scramble_command.seed
    )

    suggestions = []
    for name in result['token_scramble_suggestions']:
        obj = GeneratedName(tokens=(name,),
                            pipeline_name='scramble_collection_tokens',
                            collection_id=result['collection_id'],
                            collection_title=result['collection_title'],
                            grouping_category='related',
                            applied_strategies=[])
        obj.interpretation = []
        suggestions.append(obj)

    response = convert_to_suggestion_format(suggestions, include_metadata=scramble_command.metadata)

    logger.info(json.dumps({'endpoint': 'scramble_collection_tokens', 'request': scramble_command.model_dump()}))

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


@app.post("/find_collections_by_string", response_model=CollectionSearchResponse, tags=['collections'])
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


@app.post("/count_collections_by_string", response_model=CollectionsContainingNameCountResponse, tags=['collections'])
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


@app.post("/find_collections_by_collection", response_model=CollectionSearchResponse, tags=['collections'])
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


@app.post("/count_collections_by_member", response_model=CollectionsContainingNameCountResponse, tags=['collections'])
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


@app.post("/find_collections_by_member", response_model=CollectionsContainingNameResponse, tags=['collections'])
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


@app.post("/fetch_collection_members", response_model=CollectionCategory, tags=['collections'])
async def fetch_collection_members(fetch_command: FetchCollectionMembersRequest):
    """
    Fetch members from a collection with pagination support
    """
    result, es_response_metadata = generator_matcher.fetch_members_from_collection(
        fetch_command.collection_id,
        offset=fetch_command.offset,
        limit=fetch_command.limit
    )

    members = []
    for name in result['members']:
        obj = GeneratedName(tokens=(name,),
                          pipeline_name='fetch_collection_members',
                          collection_id=result['collection_id'],
                          collection_title=result['collection_title'],
                          grouping_category='related',
                          applied_strategies=[])
        obj.interpretation = []
        members.append(obj)

    rs = RelatedSuggestions(result['collection_title'], 
                           result['collection_id'], 
                           result['collection_members_count'])
    rs.extend(members)

    response = convert_related_to_grouped_suggestions_format(
        {result['collection_title']: rs},
        include_metadata=fetch_command.metadata
    )

    logger.info(json.dumps({
        'endpoint': 'fetch_collection_members', 
        'request': fetch_command.model_dump()
    }))

    return response[0]


@app.post("/get_collection_by_id", response_model=CollectionModel, tags=['collections'])
async def get_collection_by_id(request: GetCollectionByIdRequest):
    """
    Get information about a single collection by its ID.
    Returns 404 if collection is not found.
    Returns 503 if Elasticsearch is unavailable.
    """

    if not collections_matcher.active:
        return Response(status_code=503, content='Elasticsearch Unavailable')

    collections = collections_matcher.get_collections_by_id_list([request.collection_id])
    
    if not collections:
        return Response(status_code=404, content=f'Collection with id={request.collection_id} not found')

    collection = convert_to_collection_format(collections)[0]
    
    return collection


#TODO gc.freeze() ?
