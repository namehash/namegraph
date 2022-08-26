from typing import List, Optional
from pydantic import BaseModel, Field

from web_api import generator


class Name(BaseModel):
    name: str = Field(..., title='input name')
    metadata: bool = Field(True, title='return all the metadata in response')
    sorter: str = Field('round-robin', title='sorter algorithm',
                        regex=r'round-robin|count|length')
    min_suggestions: int = Field(100, title='minimal number of suggestions to generate',
                                 ge=1, le=generator.config.generation.limit)
    max_suggestions: int = Field(100, title='maximal number of suggestions to generate',
                                 ge=1)


class Metadata(BaseModel):
    applied_strategies: List[List[str]] = Field(
        title="sequence of steps performed in every pipeline that generated the suggestion")


class Suggestion(BaseModel):
    name: str = Field(title="suggested similar name (not label)")
    rating: str = Field(title="NameGuard rating (green or yellow)")
    metadata: Optional[Metadata] = Field(title="information how suggestion was generated",
                                         description="if metadata=False this key is absent")
