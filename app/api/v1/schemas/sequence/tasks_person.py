from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.sequence.tasks import TaskBase


class TasksPerson(TaskBase):
    person_id: Optional[int]
    person_name: Optional[str]
    to_address: Optional[str]
    email_from: Optional[str]
    mailbox_id: Optional[int]
    is_reply_to_previous_thread: Optional[bool]
    person_role_name: Optional[List[str]]
    user_avatar: Optional[str]


class TaskStatistics(BaseModel):
    total: int
    email_contact: int


class TaskList(BaseModel):
    page: Optional[int]
    per_page: Optional[int]
    total: Optional[int]
    data: List[TasksPerson]
