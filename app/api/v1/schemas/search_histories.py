from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, constr
from app.models.search_history import SEARCH_HISTORY_ENUM

class SearchHistoryItem(BaseModel):
    id: Optional[int] = None
    type: Optional[SEARCH_HISTORY_ENUM] = None
    prompt_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ListSearchHistoriesResponse(BaseModel):
    items: List[SearchHistoryItem] = []

class CreateSearchHistoryRequest(BaseModel):
    type: SEARCH_HISTORY_ENUM
    prompt_message: str = Field(max_length=1000)
    team_id: int