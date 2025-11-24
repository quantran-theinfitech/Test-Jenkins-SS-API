from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ServiceBase(BaseModel):
    corporate_number: List[str] = []
    description: Optional[str] = None
    description_romaji: Optional[str] = None
    slug_tags: Optional[List[str]] = []
    name_tags: Optional[List[str]] = []
    media_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: int
    name: Optional[str] = None
    name_romaji: Optional[str] = None
    url: Optional[str] = None


class GetServiceResponse(BaseModel):
    data: List[ServiceBase]
    total: int
    unlimited_total: int
