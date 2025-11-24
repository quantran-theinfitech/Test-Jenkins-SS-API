from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.person_exclude_collection import TypeCode


class PersonExcludeCollectionBase(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[int] = None
    type_code: Optional[TypeCode] = None
    identification_rate: Optional[float] = None
    csv_path: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class CreatePersonExcludeCollectionByIdsRequest(BaseModel):
    name: str
    description: Optional[str]
    item_ids: Optional[List[str]]


class PersonExcludeCollectionDetailResponse(BaseModel):
    name: str
    description: Optional[str] = None
    exclude_collection_count: int


class ExcludeCollectionPerson(PersonExcludeCollectionBase):
    tags: Optional[List[str]] = None


class ExcludeCollectionPersonsResponse(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: int
    data: List[ExcludeCollectionPerson]


class ListingPersonExcludeCollectionItem(PersonExcludeCollectionBase):
    persons_count: Optional[int]


class ListingPersonExcludeCollectionResponse(BaseModel):
    per_page: Optional[int] = None
    current_page: Optional[int] = None
    total: int
    data: List[ListingPersonExcludeCollectionItem]
