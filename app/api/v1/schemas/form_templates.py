from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class FormTemplateBase(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    team_id: Optional[int] = None
    created_by: Optional[int] = None


class FormTemplateRequest(BaseModel):
    title: Optional[str]
    content: Optional[str]


class ListingFormTemplateItem(FormTemplateBase):
    author: Optional[str] = None
    job_number: Optional[int] = None
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ListingTemplateResponse(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: int
    data: List[ListingFormTemplateItem]
