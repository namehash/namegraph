from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from web_api import generator


class Params(BaseModel):
    country: Optional[str] = Field(None, title='user county code',
                                   description="A two-character ISO 3166-1 country code for the country associated with the location of the requester's public IP address; might be null")
    mode: str = Field('full', title='request mode: instant, domain_detail, full',
                      regex=r'^(instant|domain_detail|full)$')


class Name(BaseModel):
    name: str = Field(title='input name')
    metadata: bool = Field(True, title='return all the metadata in response')
    sorter: str = Field('weighted-sampling', title='sorter algorithm',
                        regex=r'^(round-robin|count|length|weighted-sampling)$')
    min_suggestions: int = Field(100, title='minimal number of suggestions to generate',
                                 ge=1, le=generator.config.generation.limit)
    max_suggestions: int = Field(100, title='maximal number of suggestions to generate',
                                 ge=1)
    min_primary_fraction: float = Field(0.1, title='minimal fraction of primary names',
                                        ge=0.0, le=1.0,
                                        description='ensures at least `min_suggestions * min_primary_fraction` '
                                                    'primary names will be generated')
    params: Optional[Params] = Field(None, title='pipeline parameters',
                                     description='includes all the parameters for all nodes of the pipeline')


class Metadata(BaseModel):
    pipeline_name: str = Field(title='name of the pipeline, which has produced this suggestion')
    interpretation: list[str] = Field(title='interpretation tags',
                                      description='list of interpretation tags based on which the '
                                                  'suggestion has been generated')
    cached_status: str = Field(title='cached status',
                               description='name\'s status cached at the time of application startup')
    categories: str = Field(title='domain category',
                            description='can be either available, taken, recently released or on sale')
    cached_interesting_score: float = Field(title='cached interesting score',
                                            description='name\'s interesting score cached at the time of '
                                                        'application startup')
    applied_strategies: list[list[str]] = Field(
        title="sequence of steps performed in every pipeline that generated the suggestion"
    )
    collection: Optional[str] = Field(
        name='name of the collection',
        description='if name has been generated using a collection, '
                    'then this field would contains its name, else it is null'
    )


class Suggestion(BaseModel):
    name: str = Field(title="suggested similar name (not label)")
    metadata: Optional[Metadata] = Field(title="information how suggestion was generated",
                                         description="if metadata=False this key is absent")


# ========================= Collections API models =========================

class CollectionName(BaseModel):
    name: str = Field(title='name with .eth')
    namehash: str = Field(title='namehash of the name')

class Collection(BaseModel):
    title: str = Field(title='title of the collections')
    owner: str = Field(title='ETH address of the collection owner')
    number_of_names: int = Field(title='total number of names in the collection')
    collection_id: str = Field(title='id of the collection')
    last_updated_timestamp: int = Field(title='integer timestamp of last collection update')
    top_names: list[CollectionName] = Field(
        title='top names stored in the collection (limited by limit_names)')
    types: list[str] = Field(title='list of types to which the collection belongs')

class CollectionQueryMetadata(BaseModel):
    total_number_of_matched_collections: Optional[int] = Field(
        title='number of matched collections before trimming the result')
    processing_time_ms: float = Field(title='time elapsed for this query in milliseconds')

class BaseCollectionQueryResponse(BaseModel):
    metadata: CollectionQueryMetadata = Field(title='additional information about collection query')


# ======== Collection Search ========

class BaseCollectionSearch(BaseModel):  # instant search, domain details
    max_related_collections: int = Field(3, ge=0, title='max number of related collections to return')
    min_other_collections: int = Field(3, ge=0, title='min number of other collections to return')
    max_other_collections: int = Field(3, ge=0, title='max number of other collections to return')
    max_total_collections: int = Field(6, ge=0, title='max number of total (related + other) collections to return')

    name_diversity_ratio: Optional[float] = Field(
        0.5, ge=0.0, le=1.0,
        title='similarity value used for adding penalty to collections with similar names to other collections'
    )
    limit_names: Optional[int] = Field(10, ge=0, le=10, title='the number of names returned in each collection')

class CollectionSearchByString(BaseCollectionSearch):  # instant search, domain details
    query: str = Field(title='input query (with or without spaces) which is used to search for template collections',
                       regex=r'^[^\.]*$')
    mode: str = Field('instant', title='request mode: instant, domain_detail', regex=r'^(instant|domain_detail)$')

class CollectionSearchByCollection(BaseCollectionSearch):  # collection_details
    collection_id: str = Field(title='id of the collection used for search')

class CollectionSearchResponse(BaseCollectionQueryResponse):
    related_collections: list[Collection] = Field(title='list of related collections')
    other_collections: list[Collection] = Field(title='list of other collections (if not enough related collections)')


# ======== Collection Membership ========

class CollectionsFeaturingNameCountRequest(BaseModel):
    label: str = Field(title='label for which collection membership will be checked')

class CollectionsFeaturingNameCountResponse(BaseCollectionQueryResponse):
    count: int = Field(title='count of collections containing input name')

class CollectionsFeaturingNameRequest(BaseModel):
    label: str = Field(title='label for which membership will be checked for each collection')
    sort_order: Literal['A-Z', 'Z-A', 'AI'] = Field(
        title='order of the resulting collections (by title for alphabetic sort)')
    limit_names: Optional[int] = Field(10, title='the number of names returned in each collection')

class CollectionsFeaturingNameResponse(BaseCollectionQueryResponse):
    collections: list[Collection] = Field(title='list of public collections the provided name is a member of')
