from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PersonEducationBase(BaseModel):
    id: int
    person_uuid: Optional[str] = None
    school_name: Optional[str] = None
    major: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    current_flag: Optional[bool] = None


class ListingPersonEducaionResponse(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    data: List[PersonEducationBase]
