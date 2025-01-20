from typing import Optional, Literal, Union
from namegraph.xcollections.query_builder import SortOrder
from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo

from models import UserInfo


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
    avatar_emoji: str = Field(title='avatar emoji associated with this collection')
    avatar_image: Optional[str] = Field(None, title='avatar image associated with this collection',
                                        description='for now, is always null')


class CollectionResultMetadata(BaseModel):
    total_number_of_matched_collections: Optional[Union[int, str]] = Field(
        title='number of matched collections before trimming the result or `1000+` if more than 1000 results',
        description='return null for `count*` endpoints')
    processing_time_ms: float = Field(title='time elapsed for this query in milliseconds')
    elasticsearch_processing_time_ms: Optional[float] = Field(
        title='time elapsed for elasticsearch query in milliseconds', description='return null for `count*` endpoints')
    elasticsearch_communication_time_ms: Optional[float] = Field(
        title='time elapsed for the communication with elasticsearch from the request sending to response receiving '
              'in milliseconds')


class BaseCollectionQueryResponse(BaseModel):
    metadata: CollectionResultMetadata = Field(title='additional information about collection query response')


# ======== Collection Search ========

class BaseCollectionRequest(BaseModel):
    user_info: Optional[UserInfo] = Field(None, title='information about user making request')


class BaseCollectionSearchLimitOffsetSort(BaseCollectionRequest):
    limit_names: int = Field(10, ge=0, le=10, title='the number of names returned in each collection',
                             description='can not be greater than 10')
    offset: int = Field(0,
                        title='offset of the first collection to return (used for pagination)',
                        description='DO NOT use pagination with diversity algorithm')



class BaseCollectionSearch(BaseCollectionSearchLimitOffsetSort):
    max_related_collections: int = Field(3, ge=0, title='max number of related collections to return (for each page)',
        description='return collections at [offset, offset + max_related_collections) positions (order as in sort_order)')
    max_per_type: Optional[int] = Field(None, examples=[3],
                                        title='number of collections with the same type which are not penalized',
                                        description='* set to null if you want to disable the penalization\n'
                                                    '* if the penalization algorithm is turned on then 3 times more results (than max_related_collections) are retrieved from Elasticsearch')
    name_diversity_ratio: Optional[float] = Field(None, examples=[0.5], ge=0.0, le=1.0,
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

    @field_validator('max_other_collections')
    def max_other_between_min_other_and_max_total(cls, v: int, info: FieldValidationInfo) -> int:
        if 'min_other_collections' in info.data and info.data['min_other_collections'] > v:
            raise ValueError('min_other_collections must not be greater than max_other_collections')
        return v

    @field_validator('max_total_collections')
    def max_related_between_min_other_and_max_total(cls, v: int, info: FieldValidationInfo) -> int:
        if 'max_other_collections' in info.data and v < info.data['max_other_collections']:
            raise ValueError('max_other_collections must not be greater than max_total_collections')
        if 'min_other_collections' in info.data and 'max_related_collections' in info.data and \
                info.data['min_other_collections'] + info.data['max_related_collections'] > v:
            raise ValueError(
                'min_other_collections + max_related_collections must not be greater than max_total_collections')
        return v


class CollectionSearchByString(BaseCollectionSearchWithOther):  # instant search, domain details
    query: str = Field(title='input query (with or without spaces) which is used to search for template collections',
                       description='can not contain dots (.)',
                       pattern='^[^.]+$', examples=['zeus god'])
    mode: str = Field('instant', title='request mode: instant, domain_detail', pattern=r'^(instant|domain_detail)$')
    sort_order: Literal[SortOrder.AZ, SortOrder.ZA, SortOrder.AI, SortOrder.RELEVANCE] = Field(SortOrder.AI, title='order of the resulting collections',
                        description='* if A-Z or Z-A - sort by title (alphabetically ascending/descending)\n'
                                    '* if AI - use intelligent endpoint-specific ranking (with Learning to Rank for optimal results)\n'
                                    '* if Relevance - use relevance ranking')

class CollectionSearchByCollection(BaseCollectionSearchWithOther):  # collection_details
    collection_id: str = Field(title='id of the collection used for search', examples=['ri2QqxnAqZT7'])
    sort_order: Literal[SortOrder.AZ, SortOrder.ZA, SortOrder.RELEVANCE] = Field(SortOrder.RELEVANCE, title='order of the resulting collections',
                        description='* if A-Z or Z-A - sort by title (alphabetically ascending/descending)\n'
                                    '* if Relevance - use relevance ranking')

class CollectionSearchResponse(BaseCollectionQueryResponse):
    related_collections: list[Collection] = Field(title='list of related collections')
    other_collections: list[Collection] = Field(title='list of other collections (if not enough related collections)')


class CollectionCountByStringRequest(BaseCollectionRequest):
    query: str = Field(title='input query (with or without spaces) which is used to search for template collections',
                       description='can not contain dots (.)',
                       pattern='^[^.]+$', examples=['zeus god'])
    mode: str = Field('instant', title='request mode: instant, domain_detail', pattern=r'^(instant|domain_detail)$')

# ======== Collection Membership ========

class CollectionsContainingNameCountRequest(BaseCollectionRequest):
    label: str = Field(title='label for which collection membership will be checked', examples=['zeus'])


class CollectionsContainingNameCountResponse(BaseCollectionQueryResponse):
    count: Union[int, str] = Field(
        title='count of collections containing input label or `1000+` if more than 1000 results')


class CollectionsContainingNameRequest(BaseCollectionSearchLimitOffsetSort):
    label: str = Field(title='label for which membership will be checked for each collection', examples=['zeus'])
    mode: str = Field('instant', title='request mode: instant, domain_detail', pattern=r'^(instant|domain_detail)$')
    max_results: int = Field(3, ge=0, title='max number of collections to return (for each page)',
                 description='return collections at [offset, offset + max_results) positions (order as in sort_order)')
    sort_order: Literal[SortOrder.AZ, SortOrder.ZA, SortOrder.AI, SortOrder.RELEVANCE] = Field(SortOrder.AI, title='order of the resulting collections',
                        description='* if A-Z or Z-A - sort by title (alphabetically ascending/descending)\n'
                                    '* if AI - use intelligent endpoint-specific ranking\n'
                                    '* if Relevance - use relevance ranking')

class CollectionsContainingNameResponse(BaseCollectionQueryResponse):
    collections: list[Collection] = Field(title='list of public collections the provided label is a member of')


class GetCollectionByIdRequest(BaseCollectionRequest):
    collection_id: str = Field(title='id of the collection to fetch', examples=['ri2QqxnAqZT7'])
