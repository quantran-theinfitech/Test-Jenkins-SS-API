from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.todo import StatusCode


class ActivityLogBase(BaseModel):
    id: Optional[int] = None
    corporate_number: Optional[str] = None
    team_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    memo: Optional[str] = None
    plan_at: Optional[datetime] = None
    customer_name: Optional[str] = None
    status_code: Optional[StatusCode] = None
    type_code: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
