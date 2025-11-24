from typing import Optional

from pydantic import BaseModel


class SlackConnectionResponse(BaseModel):
    workspace_id: Optional[str] = None
    workspace_name: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    url: Optional[str] = None
    status: bool


class SlackConnectionItem(BaseModel):
    id: Optional[int]
    workspace_name: Optional[str]
    channel_name: Optional[str]
