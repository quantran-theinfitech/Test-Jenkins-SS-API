from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.companies import CompanyBase


class CompanyExcludeCollectionBase(BaseModel):
    id: int
    team_id: Optional[int] = None
    name: Optional[str] = None
    type_code: Optional[str] = None
    identification_rate: Optional[float] = None
    csv_path: Optional[str]
    created_at: Optional[datetime]
    created_by: Optional[int] = None


class ListingCompanyExcludeCollectionItem(CompanyExcludeCollectionBase):
    companies_count: Optional[int]


class ListingCompanyExcludeCollectionResponse(BaseModel):
    per_page: Optional[int] = None
    current_page: Optional[int] = None
    total: int
    data: List[ListingCompanyExcludeCollectionItem]


class ExcludeCollectionCompany(CompanyBase):
    tags: Optional[List[str]] = None


class ExcludeCollectionCompaniesResponse(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: int
    data: List[ExcludeCollectionCompany]


class ExcludeCollectionDetailResponse(BaseModel):
    name: str
    description: Optional[str] = None
    exclude_collection_count: int


class CompanyExcludeCollectionFieldName(Enum):
    INFO = "除外企業 (※会社名/会社URL/メールアドレスの@以降のドメインのいずれかを入力してください。100,000件まで登録可能です。)"
    CORPORATE_NUMBER = "法人番号"
    TEL = "電話番号"


class CreateCompanyExcludeCollectionRequest(BaseModel):
    name: str
    description: Optional[str] = None
    corporate_numbers: Optional[List[str]] = []
