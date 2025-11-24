from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ListingPlaceholderItem(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    created_by: Optional[str] = None
    usage_count: Optional[int] = 0
    created_at: Optional[datetime] = None


class ListingPlaceholderResponse(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    data: List[ListingPlaceholderItem]


class Placeholder(BaseModel):
    firstNameKanji: str
    lastNameKanji: str
    firstNameKana: str
    lastNameKana: str
    mail: str
    director: str
    departmentName: str
    tel: str
    companyURL: str
    companyName: str
    companyNameKana: str
    numberOfEmployees: int
    addressPrefecture: str
    addressUnderCity: str
    postalCode: str


class PlaceholderDetailResponse(BaseModel):
    name: str
    placeholder: Placeholder


class UpsertPlaceholderRequest(BaseModel):
    name: str
    placeholder: Placeholder
