from typing import Optional, Literal
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from pydantic.networks import IPvAnyAddress

from web_api import generator


# ======== Shared models ========

class UserInfo(BaseModel):
    user_wallet_addr: Optional[str] = Field(None, title='wallet (public) address of the user',
                                            description='might be null',
                                            examples=['1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'])
    user_ip_addr: Optional[IPvAnyAddress] = Field(None, title='IP address of the user',
                                                  description='either IPv4 or IPv6; might be null',
                                                  examples=['192.168.0.1'])
    session_id: Optional[str] = Field(None, title='', description='might be null',
                                      examples=['d6374908-94c3-420f-b2aa-6dd41989baef'])
    user_ip_country: Optional[str] = Field(None, title='user country code',
                                           description="A two-character ISO 3166-1 country code for the country associated "
                                                       "with the location of the requester's public IP address; might be null",
                                           examples=['us'])

    @field_serializer('user_ip_addr')
    def serialize_user_ip_addr(self, user_ip_addr: IPvAnyAddress, _info) -> str:
        return str(user_ip_addr)


class Metadata(BaseModel):
    pipeline_name: str = Field(title='name of the pipeline, which has produced this suggestion')
    interpretation: list[str | None] = Field(title='interpretation tags',
                                             description='list of interpretation tags based on which the '
                                                         'suggestion has been generated')
    cached_status: str = Field(title='cached status',
                               description='label\'s status cached at the time of application startup')
    categories: list[str] = Field(title='domain category',
                                  description='can be either available, taken, recently released or on sale')
    cached_sort_score: Optional[float] = Field(title='cached sort score',
                                                      description='label\'s sort score cached at the time of '
                                                                  'application startup')
    applied_strategies: list[list[str]] = Field(
        title="sequence of steps performed in every pipeline that generated the suggestion"
    )
    collection_title: Optional[str] = Field(
        title='name of the collection',
        description='if label has been generated using a collection, '
                    'then this field would contains its name, else it is null'
    )
    collection_id: Optional[str] = Field(
        title='id of the collection',
        description='if label has been generated using a collection, '
                    'then this field would contains its id, else it is null'
    )
    grouping_category: Optional[str] = Field(title='grouping category to which this suggestion belongs')


class RecursiveRelatedCollection(BaseModel):
    collection_id: str = Field(title='id of the collection')
    collection_title: str = Field(title='title of the collection')
    collection_members_count: int = Field(title='number of members in the collection')


# ======== Generator models ========

class Params(BaseModel):
    user_info: Optional[UserInfo] = Field(None, title='information about user making request')
    country: Optional[str] = Field(None, title='user country code',
                                   description="A two-character ISO 3166-1 country code for the country associated "
                                               "with the location of the requester's public IP address; might be null",
                                   examples=['us'])
    mode: str = Field('full', title='request mode: instant, domain_detail, full',
                      pattern=r'^(instant|domain_detail|full)$',
                      description='modifies global limits and sampling weights of different generators:\n'
                                  '* instant - fastest response, basic generators only\n'
                                  '* domain_detail - balanced speed/quality, expanded search\n'
                                  '* full - comprehensive generation with all generators (recommended)\n'
                                  '(for /grouped_by_category endpoint this field will be prefixed with "grouped_")')
    enable_learning_to_rank: bool = Field(True, title='enable learning to rank',
                                          description='if true, the results will be sorted by '
                                                      'learning to rank algorithm')
    label_diversity_ratio: Optional[float] = \
        Field(0.5, examples=[0.5], ge=0.0, le=1.0, title='collection diversity parameter based on labels',
              description='adds penalty to collections with similar labels to other collections\n'
                          'if null, then no penalty will be added')
    max_per_type: Optional[int] = \
        Field(2, examples=[2], ge=1, title='collection diversity parameter based on collection types',
              description='adds penalty to collections with the same type as other collections\n'
                          'if null, then no penalty will be added')


class GroupedParams(BaseModel):
    user_info: Optional[UserInfo] = Field(None, title='information about user making request')
    mode: str = Field('full', title='request mode: instant, domain_detail, full',
                      pattern=r'^(instant|domain_detail|full)$',
                      description='modifies global limits and sampling weights of different generators:\n'
                                  '* instant - fastest response, basic generators only\n'
                                  '* domain_detail - balanced speed/quality, expanded search\n'
                                  '* full - comprehensive generation with all generators (recommended)\n'
                                  '(for /grouped_by_category endpoint this field will be prefixed with "grouped_")')
    metadata: bool = Field(True, title='return all the metadata in response')


class OtherCategoriesParams(BaseModel):
    min_suggestions: int = Field(2, ge=0, le=30,
                                 title='minimal number of suggestions to generate in one specific category. '
                                       'If the number of suggestions generated for this category is below '
                                       'min_suggestions then the entire category should be filtered out from the response.')
    max_suggestions: int = Field(10, ge=0, le=30,
                                 title='maximal number of suggestions to generate in one specific category')
    model_config = ConfigDict(frozen=True)


class OtherCategoryParams(BaseModel):
    min_suggestions: int = Field(6, ge=0, le=30,
                                 title='minimal number of suggestions to generate in one specific category. '
                                       'If the number of suggestions generated for this category is below '
                                       'min_suggestions then the entire category should be filtered out from the response.')
    max_suggestions: int = Field(10, ge=0, le=30,
                                 title='maximal number of suggestions to generate in one specific category')
    min_total_suggestions: int = Field(50, ge=0, le=100,
                                       title='if not enough suggestions then "fallback generator" should be placed into another new category type called "other"'
                                             'it may be not fulfilled because of `max_suggestions` limit')
    model_config = ConfigDict(frozen=True)


class RelatedCategoryParams(BaseModel):
    max_related_collections: int = Field(6, ge=0, le=10,
                                         title='max number of related collections returned. '
                                               'If 0 it effectively turns off any related collection search.')
    max_labels_per_related_collection: int = Field(10, ge=1, le=10,
                                                  title='max number of labels returned in any related collection')
    max_recursive_related_collections: int = Field(3, ge=0, le=10,
                                                   title='Set to 0 to disable the "recursive related collection search". '
                                                         'When set to a value between 1 and 10, '
                                                         'for each related collection we find, '
                                                         'we also do a (depth 1 recursive) lookup for this many related collections '
                                                         'to the related collection.')
    enable_learning_to_rank: bool = Field(True, title='enable learning to rank',
                                          description='if true, the results will be sorted by '
                                                      'learning to rank algorithm')
    label_diversity_ratio: Optional[float] = \
        Field(0.5, examples=[0.5], ge=0.0, le=1.0, title='collection diversity parameter based on labels',
              description='adds penalty to collections with similar labels to other collections\n'
                          'if null, then no penalty will be added')
    max_per_type: Optional[int] = \
        Field(2, examples=[2], ge=1, title='collection diversity parameter based on collection types',
              description='adds penalty to collections with the same type as other collections\n'
                          'if null, then no penalty will be added')
    model_config = ConfigDict(frozen=True)


class CategoriesParams(BaseModel):
    related: RelatedCategoryParams = Field(RelatedCategoryParams(), title='related category parameters')
    wordplay: OtherCategoriesParams = Field(OtherCategoriesParams(), title='wordplay category parameters')
    alternates: OtherCategoriesParams = Field(OtherCategoriesParams(), title='alternates category parameters')
    emojify: OtherCategoriesParams = Field(OtherCategoriesParams(), title='emojify category parameters')
    community: OtherCategoriesParams = Field(OtherCategoriesParams(), title='community category parameters')
    expand: OtherCategoriesParams = Field(OtherCategoriesParams(), title='expand category parameters')
    gowild: OtherCategoriesParams = Field(OtherCategoriesParams(), title='gowild category parameters')
    other: OtherCategoryParams = Field(OtherCategoryParams(), title='other category parameters')
    model_config = ConfigDict(frozen=True)


class GroupedLabelRequest(BaseModel):
    label: str = Field(title='input label', pattern='^[^.]*$', examples=['zeus'],
                       description='* cannot contain dots (.)'
                                   '\n* if enclosed in double quotes assuming label is pre-tokenized')

    # min_primary_fraction: float = Field(0.1, title='minimal fraction of primary labels',
    #                                     ge=0.0, le=1.0,
    #                                     description='ensures at least `min_suggestions * min_primary_fraction` '
    #                                                 'primary labels will be generated')
    params: GroupedParams = Field(GroupedParams(), title='pipeline parameters',
                                  description='includes all the parameters for all nodes of the pipeline')

    categories: CategoriesParams = Field(default=CategoriesParams(),
        title='controls the results of other categories than related (except for "Other Names")')


class LabelRequest(BaseModel):
    label: str = Field(title='input label', description='cannot contain dots (.)',
                       pattern='^[^.]*$', examples=['zeus'])
    metadata: bool = Field(True, title='return all the metadata in response')
    sorter: str = Field('weighted-sampling', title='sorter algorithm',
                        pattern=r'^(round-robin|count|length|weighted-sampling)$')
    min_suggestions: int = Field(100, title='minimal number of suggestions to generate',
                                 ge=1, le=generator.config.generation.limit)
    max_suggestions: int = Field(100, title='maximal number of suggestions to generate',
                                 ge=1)
    min_primary_fraction: float = Field(0.1, title='minimal fraction of primary labels',
                                        ge=0.0, le=1.0,
                                        description='ensures at least `min_suggestions * min_primary_fraction` '
                                                    'primary labels will be generated')
    params: Optional[Params] = Field(None, title='pipeline parameters',
                                     description='includes all the parameters for all nodes of the pipeline')


class Suggestion(BaseModel):
    label: str = Field(title="suggested similar label")
    tokenized_label: list[str] = Field(title="suggested tokenization of label")
    metadata: Optional[Metadata] = Field(None, title="information how suggestion was generated",
                                         description="if metadata=False this key is absent")


class GroupingCategory(BaseModel):
    suggestions: list[Suggestion] = Field(title='generated suggestions belonging to the same category type')
    name: str = Field(title='category\'s fancy name',
                      description='for the related category it is the same as collection title')


class CollectionCategory(GroupingCategory):
    type: Literal['related'] = Field('related', title='category type',
                                     description='in CollectionCategory category type is always set to \'related\'')
    collection_id: str = Field(title='id of the collection')
    collection_title: str = Field(title='title of the collection')
    collection_members_count: int = Field(title='number of members in the collection')
    related_collections: list[RecursiveRelatedCollection] = Field(title='related collections to this collection')


class OtherCategory(GroupingCategory):
    type: Literal['wordplay', 'alternates', 'emojify', 'community', 'expand', 'gowild', 'other'] = \
        Field(title='category type',
              description='category type depends on the generator the suggestions came from')


class GroupedSuggestions(BaseModel):
    categories: list[CollectionCategory | OtherCategory] = Field(
        title='grouped suggestions',
        description='list of suggestions grouped by category type'
    )
    all_tokenizations: list[list[str]] = Field(title='all inferred tokenizations of input label')
