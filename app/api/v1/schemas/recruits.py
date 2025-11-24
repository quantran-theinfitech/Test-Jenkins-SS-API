from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.search_recruits import MediaCode


class RecruitBase(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    corporate_number: Optional[str] = None
    tags: Optional[List[str]] = None
    source_recruit_url: Optional[str] = None
    employment_type_codes: Optional[List[str]] = None
    sub_title: Optional[str] = None
    summary: Optional[str] = None
    recruit_tels: Optional[List[str]] = None
    recruit_mails: Optional[List[str]] = None
    media_code: Optional[MediaCode]
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    postal_code: Optional[str] = None
    recruitment_count: Optional[str] = None
    working_location: Optional[str] = None
    other_info: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    prefecture_codes: Optional[int] = None
    city_codes: Optional[int] = None


class GetCompanyRecruitResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[RecruitBase]
