from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel

from app.api.v1.schemas.persons import PersonBase
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.models.person_collection import StatusCode, TypeCode


class CreatePersonCollectionMode(Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class TypeDownloadPerson(str, Enum):
    CREDIT = "CREDIT"
    DOWNLOADED = "DOWNLOADED"


class PersonCollectionBase(BaseModel):
    id: int
    name: Optional[str] = None
    team_id: Optional[int] = None
    group_id: Optional[int] = None
    description: Optional[str] = None
    status_code: Optional[StatusCode] = None
    search_condition: Optional[SearchCrossRequest] = None
    step: Optional[int] = None
    type_code: Optional[TypeCode] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class CreatePersonCollectionRequest(BaseModel):
    name: str
    mode: CreatePersonCollectionMode
    group_id: Optional[int] = None
    tags: Optional[List[str]]
    description: Optional[str] = None
    search_condition: Optional[SearchCrossRequest] = None
    person_uuids: Optional[List[str]] = None
    step: Optional[int] = None
    statusCode: Optional[StatusCode] = None
    main_person_id: Optional[int] = None


class ListingPersonCollectionItem(PersonCollectionBase):
    assignees: Optional[List[str]] = None
    person_count: Optional[int] = None


class ListingPersonCollectionResponse(BaseModel):
    page: Optional[int]
    per_page: Optional[int]
    total: int
    data: List[ListingPersonCollectionItem]


class ListingCollectionDetailItem(PersonBase):
    tags: Optional[List[Union[str, None]]]
    status_code: Optional[StatusCode] = None


class ListingCollectionDetailResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[ListingCollectionDetailItem]


class UpdatePersonCollectionRequest(BaseModel):
    name: Optional[str] = None
    status_code: Optional[StatusCode]


class PersonCollectionResponse(BaseModel):
    id: Optional[int] = None
    status_code: Optional[StatusCode] = None


class AddPersonCollectionItemsRequest(BaseModel):
    type_download: Optional[TypeDownloadPerson]
    collection_names: Optional[List[str]] = None
    uuids: Optional[List[str]] = None
    search_condition: Optional[SearchCrossRequest] = None
