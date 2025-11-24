from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.search_cross import SearchCrossRequest


class SearchConditionBase(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    owner_code: Optional[str] = None
    name: Optional[str] = None
    conditions: Optional[SearchCrossRequest] = None


class UpdateSearchConditionRequest(BaseModel):
    name: Optional[str] = None
    conditions: Optional[SearchCrossRequest] = None


class RefineQueryRequest(BaseModel):
    query: str
    type: str


class RefineQueryResponse(BaseModel):
    input_query: str
    refined_query: List[str]
