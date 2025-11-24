from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.todo import StatusCode


class TodoBase(BaseModel):
    id: int
    title: Optional[str] = None
    content: Optional[str] = None
    memo: Optional[str] = None
    plan_at: Optional[datetime] = None
    customer_name: Optional[str] = None
    status_code: Optional[StatusCode] = None
    type_code: Optional[str] = None
    assignee_id: Optional[int] = None
    company_id: Optional[int] = None


class CreateTodoRequest(BaseModel):
    title: Optional[str]
    content: Optional[str]
    memo: Optional[str]
    plan_at: Optional[datetime]
    customer_name: Optional[str]
    status_code: Optional[StatusCode]
    type_code: Optional[str]
    assignee_id: Optional[int]
    corporate_number: Optional[str]


class UpdateTodoRequest(BaseModel):
    title: Optional[str]
    content: Optional[str]
    memo: Optional[str]
    plan_at: Optional[datetime]
    customer_name: Optional[str]
    status_code: Optional[StatusCode]
    type_code: Optional[str]
    assignee_id: Optional[int]
