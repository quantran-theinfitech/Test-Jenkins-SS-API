from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GetNoteDetailResponse(BaseModel):
    id: int
    content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreateNoteRequest(BaseModel):
    step_id: int
    content: str


class UpdateNoteRequest(BaseModel):
    content: str
