from typing import Optional

from pydantic import BaseModel


class UpdateMailTemplateRequest(BaseModel):
    title: Optional[str]
    content: str
    is_reply_to_previous_thread: bool
    is_include_signature: bool


class DetailMailTemplateResponse(BaseModel):
    id: int
    title: Optional[str]
    content: Optional[str]
    is_reply_to_previous_thread: Optional[bool] = False
    is_include_signature: Optional[bool] = False
    total_days_on_step: Optional[int]
