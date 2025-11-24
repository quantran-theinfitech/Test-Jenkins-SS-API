from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class EventType(str, Enum):
    EXPO = "EXPO"
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"


class EventBase(BaseModel):
    id: int
    name: Optional[str] = None
    content: Optional[str] = None
    corporate_number: Optional[str] = None
    media_code: Optional[str] = None
    source_event_url: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    type: Optional[EventType] = None
    address: Optional[str] = None
    image: Optional[str] = None
    tool: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GetEventResponse(BaseModel):
    data: List[EventBase]
    total: int
    unlimited_total: int
