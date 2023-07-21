from typing import Optional, Literal
from pydantic import BaseModel, Field

from web_api import generator


class Params(BaseModel):
    country: Optional[str] = Field(None, title='user county code',
                                   description="A two-character ISO 3166-1 country code for the country associated with the location of the requester's public IP address; might be null",
                                   examples=['us'])
    mode: str = Field('full', title='request mode: instant, domain_detail, full',
                      pattern=r'^(instant|domain_detail|full)$',
                      description='for /grouped_by_category endpoint this field will be prefixed with "grouped_"')


class Name(BaseModel):
    name: str = Field(title='input name', examples=['zeus'])
    metadata: bool = Field(True, title='return all the metadata in response')
    sorter: str = Field('weighted-sampling', title='sorter algorithm',
                        pattern=r'^(round-robin|count|length|weighted-sampling)$')
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
    categories: list[str] = Field(title='domain category',
                                  description='can be either available, taken, recently released or on sale')
    cached_interesting_score: Optional[float] = Field(title='cached interesting score',
                                            description='name\'s interesting score cached at the time of '
                                                        'application startup')
    applied_strategies: list[list[str]] = Field(
        title="sequence of steps performed in every pipeline that generated the suggestion"
    )
    collection_title: Optional[str] = Field(
        title='name of the collection',
        description='if name has been generated using a collection, '
                    'then this field would contains its name, else it is null'
    )
    collection_id: Optional[str] = Field(  # todo: maybe bundle collection's title and id together
        title='id of the collection',
        description='if name has been generated using a collection, '
                    'then this field would contains its id, else it is null'
    )
    grouping_category: Optional[str] = Field(title='grouping category to which this suggestion belongs')


class Suggestion(BaseModel):
    name: str = Field(title="suggested similar name (not label)")
    metadata: Optional[Metadata] = Field(title="information how suggestion was generated",
                                         description="if metadata=False this key is absent")


class GroupingCategory(BaseModel):
    suggestions: list[Suggestion] = Field(title='generated suggestions belonging to the same category type')


class CollectionCategory(GroupingCategory):
    type: Literal['related'] = Field('related', title='category type',
                                     description='in CollectionCategory category type is always set to \'related\'')
    collection_id: str = Field(title='id of the collection')
    collection_title: str = Field(title='title of the collection')


class OtherCategory(GroupingCategory):
    type: Literal['wordplay', 'alternates', 'emojify', 'community', 'expand', 'gowild'] = \
        Field(title='category type',
              description='category type depends on the generator the suggestions came from')
