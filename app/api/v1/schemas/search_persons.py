from typing import List, Optional, Union

from pydantic import BaseModel


class EsPersonBase(BaseModel):
    id: Optional[int]
    name: Optional[Union[str, None]]
    uuid: Optional[Union[str, None]]
    intro: Optional[Union[str, None]]
    role_name: Optional[List[Union[str, None]]]
    bio: Optional[Union[str, None]]
    role_code: Optional[Union[str, None]]
    role_group_codes: Optional[List[Union[str, None]]]
    linkedin_url: Optional[Union[str, None]]
    twitter_url: Optional[Union[str, None]]
    github_url: Optional[Union[str, None]]
    note_url: Optional[Union[str, None]]
    fb_url: Optional[Union[str, None]]
    wantedly_url: Optional[Union[str, None]] = None
    skills: Optional[Union[str, None]]
    wantedly_id: Optional[Union[str, None]]
    linkedin_internal_id: Optional[Union[str, None]]
    address: Optional[Union[str, None]]
    corporate_number: Optional[List[Union[str, None]]]
    company_name: Optional[List[Union[str, None]]]
    email: Optional[Union[str, None]]


class SearchPersonItem(EsPersonBase):
    downloaded_flag: bool
    available_fields: Optional[List[str]]


class SearchPersonResponse(BaseModel):
    page: int
    per_page: int
    total: int
    unlimited_total: int
    data: List[SearchPersonItem]


class GetListUUIDs(BaseModel):
    uuids: List[str]


class GetTotalPersonLockAndUnlockResponse(BaseModel):
    total_lock: int
    total_unlock: int
    total: int
