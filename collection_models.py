from typing import Optional, Literal, Union
from pydantic import BaseModel, Field, validator


class CollectionName(BaseModel):
    name: str = Field(title='name with `.eth`')
    namehash: str = Field(title='namehash of the name')


class Collection(BaseModel):
    collection_id: str = Field(title='id of the collection')
    title: str = Field(title='title of the collection')
    owner: str = Field(title='ETH address of the collection owner')
    number_of_names: int = Field(title='total number of names in the collection')
    last_updated_timestamp: int = Field(title='timestamp in milliseconds of last collection update')
    top_names: list[CollectionName] = Field(
        title='top names stored in the collection (limited by `limit_names`)', description='can not be greater than 10')
    types: list[str] = Field(title='list of types to which the collection belongs',
                             description='example of type is `human`')


class CollectionResultMetadata(BaseModel):
    total_number_of_matched_collections: Optional[Union[int, str]] = Field(
        title='number of matched collections before trimming the result or `1000+` if more than 1000 results',
        description='return null for `count*` endpoints')
    processing_time_ms: float = Field(title='time elapsed for this query in milliseconds')
    elasticsearch_processing_time_ms: Optional[float] = Field(
        title='time elapsed for elasticsearch query in milliseconds', description='return null for `count*` endpoints')
    elasticsearch_communication_time_ms: float = Field(
        title='time elapsed for the communication with elasticsearch from the request sending to response receiving '
              'in milliseconds')


class BaseCollectionQueryResponse(BaseModel):
    metadata: CollectionResultMetadata = Field(title='additional information about collection query response')


# ======== Collection Search ========

class BaseCollectionSearchLimitOffsetSort(BaseModel):
    limit_names: int = Field(10, ge=0, le=10, title='the number of names returned in each collection',
                             description='can not be greater than 10')
    offset: int = Field(0,
                        title='offset of the first collection to return (used for pagination)',
                        description='DO NOT use pagination with diversity algorithm')
    sort_order: Literal['A-Z', 'Z-A', 'AI'] = Field('AI', title='order of the resulting collections',
                        description='* if A-Z or Z-A - sort by title (asc/desc)\n'
                                    '* if AI - use intelligent, endpoint-specific sort approach')


class BaseCollectionSearch(BaseCollectionSearchLimitOffsetSort):
    max_related_collections: int = Field(3, ge=0, title='max number of related collections to return (for each page)',
        description='return collections at [offset, offset + max_related_collections) positions (order as in sort_order)')
    max_per_type: Optional[int] = Field(None, example=3,
                                        title='number of collections with the same type which are not penalized',
                                        description='* set to null if you want to disable the penalization\n'
                                                    '* if the penalization algorithm is turned on then 3 times more results (than max_related_collections) are retrieved from Elasticsearch')
    name_diversity_ratio: Optional[float] = Field(None, example=0.5, ge=0.0, le=1.0,
        title='similarity value used for adding penalty to collections with similar names to other collections',
        description='* if more than name_diversity_ratio % of the names have already been used, penalize the collection\n'
                    '* set to null if you want disable the penalization\n'
                    '* if the penalization algorithm is turned on then 3 times more results (than `max_related_collections`) '
                    'are retrieved from Elasticsearch'
    )


class BaseCollectionSearchWithOther(BaseCollectionSearch):  # instant search, domain details
    min_other_collections: int = Field(0, ge=0, title='min number of other collections to return')
    max_other_collections: int = Field(3, ge=0, title='max number of other collections to return',
                                       description='constraint: \n'
                                       '* min_other_collections <= max_other_collections\n'
                                       '\nif not met, 422 status code is returned')
    max_total_collections: int = Field(6, ge=0, title='max number of total (related + other) collections to return',
                                       description='constraints: \n'
                                       '* max_other_collections <= max_total_collections\n'
                                       '* min_other_collections + max_related_collections  <= max_total_collections\n'
                                       '\nif not met, 422 status code is returned')

    @validator('max_other_collections')
    def max_other_between_min_other_and_max_total(cls, v: int, values, **kwargs) -> int:
        if 'min_other_collections' in values and values['min_other_collections'] > v:
            raise ValueError('min_other_collections must not be greater than max_other_collections')
        return v

    @validator('max_total_collections')
    def max_related_between_min_other_and_max_total(cls, v: int, values, **kwargs) -> int:
        if 'max_other_collections' in values and v < values['max_other_collections']:
            raise ValueError('max_other_collections must not be greater than max_total_collections')
        if 'min_other_collections' in values and 'max_related_collections' in values and \
                values['min_other_collections'] + values['max_related_collections'] > v:
            raise ValueError(
                'min_other_collections + max_related_collections must not be greater than max_total_collections')
        return v


class CollectionSearchByString(BaseCollectionSearchWithOther):  # instant search, domain details
    query: str = Field(title='input query (with or without spaces) which is used to search for template collections',
                       description='can not contain dots (.)',
                       regex='^[^.]+$', example='zeus god')
    mode: str = Field('instant', title='request mode: instant, domain_detail', regex=r'^(instant|domain_detail)$')


class CollectionSearchByCollection(BaseCollectionSearchWithOther):  # collection_details
    collection_id: str = Field(title='id of the collection used for search', example='Q6607079')


class CollectionSearchResponse(BaseCollectionQueryResponse):
    related_collections: list[Collection] = Field(title='list of related collections')
    other_collections: list[Collection] = Field(title='list of other collections (if not enough related collections)')

class CollectionCountByStringRequest(BaseModel):
    query: str = Field(title='input query (with or without spaces) which is used to search for template collections',
                       description='can not contain dots (.)',
                       regex='^[^.]+$', example='zeus god')
    mode: str = Field('instant', title='request mode: instant, domain_detail', regex=r'^(instant|domain_detail)$')

# ======== Collection Membership ========

class CollectionsContainingNameCountRequest(BaseModel):
    label: str = Field(title='label for which collection membership will be checked', example='zeus')


class CollectionsContainingNameCountResponse(BaseCollectionQueryResponse):
    count: Union[int, str] = Field(
        title='count of collections containing input label or `1000+` if more than 1000 results')


class CollectionsContainingNameRequest(BaseCollectionSearchLimitOffsetSort):
    label: str = Field(title='label for which membership will be checked for each collection', example='zeus')
    mode: str = Field('instant', title='request mode: instant, domain_detail', regex=r'^(instant|domain_detail)$')
    max_results: int = Field(3, ge=0, title='max number of collections to return (for each page)',
                 description='return collections at [offset, offset + max_results) positions (order as in sort_order)')


class CollectionsContainingNameResponse(BaseCollectionQueryResponse):
    collections: list[Collection] = Field(title='list of public collections the provided label is a member of')
