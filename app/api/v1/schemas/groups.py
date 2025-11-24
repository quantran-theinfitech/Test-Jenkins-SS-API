from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.collections import Collection
from app.api.v1.schemas.person_collections import PersonCollectionBase


class GroupBase(BaseModel):
    id: Optional[int] = None
    team_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    default_flag: Optional[bool] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[datetime] = None
    created_at: Optional[datetime] = None
    created_by: Optional[datetime] = None


class CreateGroupRequest(BaseModel):
    name: str
    description: Optional[str] = None


class GetGroupResponse(GroupBase):
    per_page: Optional[int] = None
    current_page: Optional[int] = None
    total: int
    collections: List[Collection]


class ListingGroupItem(GroupBase):
    company_collection_count: Optional[int] = 0
    person_collection_count: Optional[int] = 0


class ListingGroupResponse(BaseModel):
    per_page: Optional[int] = None
    current_page: Optional[int] = None
    total: int
    data: List[ListingGroupItem]


class ListingPersonCollectionsResponse(BaseModel):
    per_page: Optional[int] = None
    current_page: Optional[int] = None
    total: int
    data: Optional[List[PersonCollectionBase]] = None
