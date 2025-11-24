from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PersonCareerBase(BaseModel):
    id: int
    person_uuid: str
    company_name: Optional[str] = None
    company_id: Optional[int] = None
    role_code: Optional[str] = None
    role_name: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    current_flag: Optional[bool] = None
    hp_url: Optional[str] = None


class ListingPersonCareerResponse(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    data: List[PersonCareerBase]
