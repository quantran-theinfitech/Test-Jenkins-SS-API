from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class SearchType(str, Enum):
    industry = "industry"
    job_category = "job_category"
    location = "location"


class SearchAllRequest(BaseModel):
    type: Optional[SearchType] = None
    keyword: Optional[str] = None


class SearchAllBase(BaseModel):
    field: Optional[str] = None
    field_code: Optional[str] = None
    sub_field: Optional[str] = None
    sub_field_code: Optional[str] = None


class SearchAllResponse(BaseModel):
    keyword: str
    data: List[SearchAllBase]
