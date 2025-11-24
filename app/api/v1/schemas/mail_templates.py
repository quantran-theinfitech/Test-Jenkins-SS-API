from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MailTemplateBase(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    team_id: Optional[int] = None
    created_by: Optional[int] = None


class MailTemplateRequest(BaseModel):
    title: Optional[str]
    content: Optional[str]


class ListingMailTemplateItem(MailTemplateBase):
    author: Optional[str] = None
    job_number: Optional[int] = None
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ListingTemplateResponse(BaseModel):
    per_page: Optional[int] = None
    current_page: Optional[int] = None
    total: int
    data: List[ListingMailTemplateItem]
