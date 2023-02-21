from typing import List, Optional
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
    # pipeline_name: str = Field(title='name of the pipeline, which has produced this suggestion')
    # interpretation: list[str] = Field(title='interpretation tags',
    #                                   description='list of interpretation tags based on which the '
    #                                               'suggestion has been generated')
    # category: str = Field(title='domain category',
    #                       description='can be either available, taken, recently released or on sale')
    applied_strategies: List[List[str]] = Field(
        title="sequence of steps performed in every pipeline that generated the suggestion")


class Suggestion(BaseModel):
    name: str = Field(title="suggested similar name (not label)")
    metadata: Optional[Metadata] = Field(title="information how suggestion was generated",
                                         description="if metadata=False this key is absent")
