from typing import List
from pydantic import BaseModel, Field


class Name(BaseModel):
    name: str = Field(title='input name')
    min_suggestions: int = Field(title='minimal number of suggestions to generate',
                                 ge=1,
                                 default=None)
    max_suggestions: int = Field(title='maximal number of suggestions to generate',
                                 ge=1,
                                 default=None)


class Result(BaseModel):
    """
    Input name might be truncated if is too long.
    """
    advertised: List[str] = []
    secondary: List[str] = []
    primary: List[str] = []


class Metadata(BaseModel):
    applied_strategies: List[List[str]]


class Suggestion(BaseModel):
    name: str
    metadata: Metadata


class ResultWithMetadata(BaseModel):
    advertised: List[Suggestion] = []
    secondary: List[Suggestion] = []
    primary: List[Suggestion] = []
