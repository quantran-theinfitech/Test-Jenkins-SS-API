from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TrackingUrlBase(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    team_id: Optional[int] = None
    original_url: Optional[str] = None
    shorten_path: Optional[str] = None
    tracking_flag: Optional[int] = None
    created_at: Optional[datetime] = None


class ListingTrackingUrlItem(TrackingUrlBase):
    created_by: Optional[str] = None


class ListingTrackingUrlResponse(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    data: List[ListingTrackingUrlItem]


class GetTrackingUrlDetail(TrackingUrlBase):
    clickable_count: Optional[int] = None


class CreateTrackingUrlRequest(BaseModel):
    name: str
    original_url: str
    tracking_flag: Optional[int] = 0


class CreateTrackingUrlResponse(TrackingUrlBase):
    created_by: Optional[int] = None
