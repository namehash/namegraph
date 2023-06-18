from typing import Optional, Literal
from pydantic import BaseModel, Field


class CollectionName(BaseModel):
    name: str = Field(title='name with .eth')
    namehash: str = Field(title='namehash of the name')


class Collection(BaseModel):
    collection_id: str = Field(title='id of the collection')
    title: str = Field(title='title of the collections')
    owner: str = Field(title='ETH address of the collection owner')
    number_of_names: int = Field(title='total number of names in the collection')
    last_updated_timestamp: int = Field(title='integer timestamp of last collection update')
    top_names: list[CollectionName] = Field(
        title='top names stored in the collection (limited by limit_names)')
    types: list[str] = Field(title='list of types to which the collection belongs')


class CollectionResultMetadata(BaseModel):
    total_number_of_matched_collections: Optional[int] = Field(
        title='number of matched collections before trimming the result or "+1000" if more than 1000 results')  # TODO
    processing_time_ms: float = Field(title='time elapsed for this query in milliseconds')
    elasticsearch_processing_time_ms: Optional[float] = Field(
        title='time elapsed for elasticsearch query in milliseconds')


class BaseCollectionQueryResponse(BaseModel):
    metadata: CollectionResultMetadata = Field(title='additional information about collection query response')


# ======== Collection Search ========

class BaseCollectionSearch(BaseModel):  # instant search, domain details
    max_related_collections: int = Field(3, ge=0, title='max number of related collections to return')
    min_other_collections: int = Field(3, ge=0, title='min number of other collections to return')
    max_other_collections: int = Field(3, ge=0, title='max number of other collections to return')
    max_total_collections: int = Field(6, ge=0, title='max number of total (related + other) collections to return')
    max_per_type: Optional[int] = Field(3, title='number of collections with the same type which are not penalized; set to null if you want disable the penalization')
    name_diversity_ratio: Optional[float] = Field(
        0.5, ge=0.0, le=1.0,
        title='similarity value used for adding penalty to collections with similar names to other collections; if more than name_diversity_ration of the names have already been used, penalize the collection; set to null if you want disable the penalization'
    )
    limit_names: int = Field(10, ge=0, le=10, title='the number of names returned in each collection')


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

class CollectionsContainingNameCountRequest(BaseModel):
    label: str = Field(title='label for which collection membership will be checked')


class CollectionsContainingNameCountResponse(BaseCollectionQueryResponse):
    count: int = Field(title='count of collections containing input name')


class CollectionsContainingNameRequest(BaseModel):
    label: str = Field(title='label for which membership will be checked for each collection')
    sort_order: Literal['A-Z', 'Z-A', 'AI'] = Field(
        title='order of the resulting collections (by title for alphabetic sort)')
    limit_names: Optional[int] = Field(10, ge=0, le=10, title='the number of names returned in each collection')
    mode: str = Field('instant', title='request mode: instant, domain_detail', regex=r'^(instant|domain_detail)$')


class CollectionsContainingNameResponse(BaseCollectionQueryResponse):
    collections: list[Collection] = Field(title='list of public collections the provided label is a member of')
