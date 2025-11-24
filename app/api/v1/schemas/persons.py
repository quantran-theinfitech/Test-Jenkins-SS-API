from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel
from sqlmodel import Field

from app.api.v1.schemas.search_cross import SearchCrossRequest


class PersonBase(BaseModel):
    id: int = None
    name: Optional[str] = None
    uuid: str
    role_code: Optional[str] = None
    role_name: Optional[List[Union[str, None]]]
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None
    note_url: Optional[str] = None
    fb_url: Optional[str] = None
    wantedly_url: Optional[str] = None
    skills: Optional[str] = None
    wantedly_id: Optional[str] = None
    linkedin_internal_id: Optional[str] = None
    address: Optional[str] = None
    intro: Optional[str] = None
    role_group_codes: Optional[List[Union[str, None]]]
    company_name: Optional[List[Union[str, None]]]
    bio: Optional[str] = None
    corporate_number: Optional[List[Union[str, None]]]


class ListingDownloadedKeymansResponse(BaseModel):
    page: int
    per_page: int
    total: int
    unlimited_total: int
    data: List[PersonBase]


class PersonDetailResponse(PersonBase):
    downloaded_flag: Optional[bool] = None
    available_fields: Optional[List[str]] = []


class SaveSearchPersonConditionRequest(BaseModel):
    name: str
    conditions: SearchCrossRequest


class DownloadPersonRequest(BaseModel):
    person_uuids: List[str] = Field(...)


class DownloadPersonMode(Enum):
    RANDOM = "RANDOM"
    EXACT = "EXACT"


class DownloadPersonConditionRequest(BaseModel):
    search_condition: SearchCrossRequest
    mode: DownloadPersonMode


class PersonsStatisticsResponse(BaseModel):
    total: int
    unlimited_total: int
    linkedin_url: int
    twitter_url: int
    github_url: int
    fb_url: int
    wantedly_url: int


class RoleGroupCode(str, Enum):
    CXO = "CXO"
    Director = "Director"
    Other = "Other"


class RoleGroupCodeResponse(Enum):
    CXO = "CXO/役員"
    Director = "Director+"
    Other = "Other"
