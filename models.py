from typing import List
from pydantic import BaseModel, Field

from web_api import generator


class Name(BaseModel):
    name: str = Field(title='input name')
    sorter: str = Field(title='sorter algorithm', default='round-robin',
                        regex=r'round-robin|count|length')
    min_suggestions: int = Field(title='minimal number of suggestions to generate',
                                 ge=1, le=generator.config.generation.limit, default=None)
    max_suggestions: int = Field(title='maximal number of suggestions to generate',
                                 ge=1, default=None)


class Result(BaseModel):
    """
    Input name might be truncated if is too long.
    """
    advertised: List[str] = []
    secondary: List[str] = []
    primary: List[str] = []


class Metadata(BaseModel):
    applied_strategies: List[List[str]] = Field(
        title="lis of steps performed in every pipeline that generated the suggestion")


class Suggestion(BaseModel):
    name: str = Field(title="suggested similar name (not label)")
    nameguard_rating: str = Field(title="NameGuard rating (green or yellow)")
    metadata: Metadata = Field(title="information how suggestion was generated")


class ResultWithMetadata(BaseModel):
    advertised: List[Suggestion] = []
    secondary: List[Suggestion] = []
    primary: List[Suggestion] = []
