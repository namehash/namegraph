from typing import List, Optional
from pydantic import BaseModel, Field

from web_api import generator


class NormalizerParams(BaseModel):
    pass


class TokenizerParams(BaseModel):
    pass


class GeneratorParams(BaseModel):
    # todo desription of the parameter after defining...
    country: str  # todo some validation for country code? no sense to add until defined by the client


class FilterParams(BaseModel):
    pass


class PipelineParams(BaseModel):
    normalizer: NormalizerParams = Field(dict())
    tokenizer: TokenizerParams = Field(dict())
    generator: GeneratorParams = Field(dict())
    filter: FilterParams = Field(dict())


class Name(BaseModel):
    name: str = Field(title='input name')
    metadata: bool = Field(True, title='return all the metadata in response')
    sorter: str = Field('weighted-sampling', title='sorter algorithm',
                        regex=r'round-robin|count|length|weighted-sampling')
    min_suggestions: int = Field(100, title='minimal number of suggestions to generate',
                                 ge=1, le=generator.config.generation.limit)
    max_suggestions: int = Field(100, title='maximal number of suggestions to generate',
                                 ge=1)
    min_primary_fraction: float = Field(0.1, title='minimal fraction of primary names',
                                        ge=0.0, le=1.0,
                                        description='ensures at least `min_suggestions * min_primary_fraction` '
                                                    'primary names will be generated')
    params: Optional[PipelineParams] = Field(None, title='pipeline parameters',
                                             description='includes all the parameters for all nodes of the pipeline')


class Metadata(BaseModel):
    applied_strategies: List[List[str]] = Field(
        title="sequence of steps performed in every pipeline that generated the suggestion")


class Suggestion(BaseModel):
    name: str = Field(title="suggested similar name (not label)")
    metadata: Optional[Metadata] = Field(title="information how suggestion was generated",
                                         description="if metadata=False this key is absent")
