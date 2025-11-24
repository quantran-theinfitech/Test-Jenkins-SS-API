from datetime import datetime
from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel


class PressReleaseBase(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    media_code: Optional[str] = None
    source_article_url: Optional[str] = None
    keyword_texts: Optional[List[str]] = None
    keyword_urls: Optional[List[str]] = None
    business_category_texts: Optional[List[str]] = None
    business_category_urls: Optional[List[str]] = None
    corporate_number: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    posted_at: Optional[datetime] = None


class ListingPressReleasesResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[PressReleaseBase]


class PRbusinessCategoryItem(BaseModel):
    id: int
    name: str


class ListingPRbusinessCategoryResponse(BaseModel):
    total: int
    page: int
    per_page: int
    data: List[PRbusinessCategoryItem]


class ListingPRbusinessCategoryByIdsResponse(BaseModel):
    data: List[PRbusinessCategoryItem]


class ListingPRbusinessCategoryQueryParams(BaseModel):
    per_page: int = Query(default=10, ge=1)
    page: int = Query(default=1, ge=1)
    keyword: Optional[str] = Query(default=None)
