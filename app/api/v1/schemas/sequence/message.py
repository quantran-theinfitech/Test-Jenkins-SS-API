from typing import List, Optional

from pydantic import BaseModel

from app.models.sequence.content_items import ContentItemsType


class GetMessageItemDetailBase(BaseModel):
    id: Optional[int]
    type: Optional[ContentItemsType] = None
    content: Optional[str] = None
    order: Optional[int] = None
    file_name: Optional[str] = None
    content_size: Optional[int] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None


class GetMessageTemplateDetailResponse(BaseModel):
    id: int
    title: Optional[str]
    message_items: Optional[List[GetMessageItemDetailBase]]


class UpdateMessageItemDetail(BaseModel):
    id: Optional[int]
    type: Optional[ContentItemsType] = None
    content: Optional[str] = None
    order: Optional[int]
    file_name: Optional[str] = None
    content_size: Optional[int] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None


class UpdateMessageTemplateRequest(BaseModel):
    title: Optional[str]
    message_items: Optional[List[UpdateMessageItemDetail]]
