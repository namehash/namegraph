from datetime import datetime
from typing import Optional, Literal, Union
from pydantic import BaseModel, Field, PositiveInt, field_validator
from pydantic_core.core_schema import FieldValidationInfo

from namegraph.xcollections.query_builder import SortOrder
from models import UserInfo, Metadata, RecursiveRelatedCollection


class CollectionName(BaseModel):  # todo: change to CollectionLabel
    name: str = Field(title='label from a collection')  # todo: change to label
    namehash: str = Field(title='namehash of the name')  # todo: remove namehash (also from the collections code)


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


# ======== Suggestions from collections ========

class SuggestionFromCollection(BaseModel):
    name: str = Field(title="label from a collection")  # todo: change to label
    tokenized_label: list[str] = Field(title="original tokenization of label")
    metadata: Optional[Metadata] = Field(None, title="information how suggestion was generated",
                                         description="if metadata=False this key is absent")


class CollectionWithSuggestions(BaseModel):
    suggestions: list[SuggestionFromCollection] = Field(title='suggestions from a collection')
    name: str = Field(title='collection title', description='kept for backwards compatibility')  # todo:  remove field
    type: Literal['related'] = Field('related', title='category type (always set to \'related\')', 
                                     description='kept for backwards compatibility')  # todo: remove field
    collection_id: str = Field(title='id of the collection')
    collection_title: str = Field(title='title of the collection')
    collection_members_count: int = Field(title='number of members in the collection')
    related_collections: list[RecursiveRelatedCollection] = Field(title='related collections to this collection')


class SampleCollectionMembers(BaseModel):
    user_info: Optional[UserInfo] = Field(None, title='information about user making request')
    collection_id: str = Field(title='id of the collection to sample from', examples=['qdeq7I9z0_jv'])
    metadata: bool = Field(True, title='return all the metadata in response')
    max_sample_size: int = Field(title='the maximum number of members to sample', ge=1, le=100,
                                 description='if the collection has less members than max_sample_size, '
                                             'all the members will be returned', examples=[5])
    seed: int = Field(default_factory=lambda: int(datetime.now().timestamp()),
                      title='seed for random number generator',
                      description='if not provided (but can\'t be null), random seed will be generated')


class Top10CollectionMembersRequest(BaseModel):
    user_info: Optional[UserInfo] = Field(None, title='information about user making request')
    collection_id: str = Field(title='id of the collection to fetch names from', examples=['ri2QqxnAqZT7'])
    metadata: bool = Field(True, title='return all the metadata in response')
    max_recursive_related_collections: int = Field(3, ge=0, le=10,
                                                   title='Set to 0 to disable the "recursive related collection search". '
                                                         'When set to a value between 1 and 10, '
                                                         'for each related collection we find, '
                                                         'we also do a (depth 1 recursive) lookup for this many related collections '
                                                         'to the related collection.')


class ScrambleCollectionTokens(BaseModel):
    user_info: Optional[UserInfo] = Field(None, title='information about user making request')
    collection_id: str = Field(title='id of the collection to take tokens from', examples=['3OB_f2vmyuyp'])
    metadata: bool = Field(True, title='return all the metadata in response')
    method: Literal['left-right-shuffle', 'left-right-shuffle-with-unigrams', 'full-shuffle'] = \
        Field('left-right-shuffle-with-unigrams', title='method used to scramble tokens and generate new suggestions',
  description='* left-right-shuffle - tokenize names as bigrams and shuffle the right-side tokens (do not use unigrams)'
              '\n* left-right-shuffle-with-unigrams - same as above, but with some tokens swapped with unigrams'
              '\n* full-shuffle - shuffle all tokens from bigrams and unigrams and create random bigrams')
    n_top_members: int = Field(25, title='number of collection\'s top members to include in scrambling', ge=1)
    max_suggestions: Optional[PositiveInt] = Field(10, title='maximal number of suggestions to generate',
  examples=[10], description='must be a positive integer or null\n* number of generated suggestions will be '
                             '`max_suggestions` or less (exactly `max_suggestions` if there are enough members)\n'
                             '* if null, no tokens are repeated')
    seed: int = Field(default_factory=lambda: int(datetime.now().timestamp()),
                      title='seed for random number generator',
                      description='if not provided (but can\'t be null), random seed will be generated')


class FetchCollectionMembersRequest(BaseModel):
    collection_id: str = Field(
        title='id of the collection to fetch members from', examples=['ri2QqxnAqZT7']
    )
    offset: int = Field(
        0, title='number of members to skip', description='used for pagination', ge=0
    )
    limit: int = Field(
        10, title='maximum number of members to return', description='used for pagination', ge=1,
    )
    metadata: bool = Field(
        True, title='return all the metadata in response'
    )


# refactor models plan:
#  [x] apply easy renamings
#  [x] separate request forming functions
#  3. adjust collection models and their request forming functions
#  4. check josiah renamings
