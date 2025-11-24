import enum
from datetime import datetime
from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel, Field

from app.api.v1.schemas.sequence.campaigns import ContentTemplateBase
from app.api.v1.schemas.sequence.mail_histories import ScheduleType
from app.models.sequence.task import Priority as TaskPriority
from app.models.sequence.task import TaskStatus, TaskType


class TaskBase(BaseModel):
    id: int
    sequence_person_id: Optional[int] = None
    sequence_step_id: Optional[int] = None
    team_id: Optional[int] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    sequence_campaign_id: Optional[int] = None
    mail_template: Optional[ContentTemplateBase] = None
    task_type: Optional[TaskType] = None
    priority: Optional[TaskPriority] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    checkbox_status_default: Optional[bool] = None

    class config:
        orm_mode = True


class UpdateTaskList(BaseModel):
    data: List[TaskBase]


class AddTaskRequest(BaseModel):
    sequence_person_id: int
    task_type: TaskType
    priority: TaskPriority
    title: str
    description: str
    due_date: Optional[datetime] = Field(default_factory=datetime.now)


class UpdateTaskRequest(BaseModel):
    task_ids: Optional[List[int]] = None
    task_type: Optional[TaskType] = None
    priority: Optional[TaskPriority] = None
    title: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[ScheduleType] = None
    custom_datetime: Optional[datetime] = None
    status: Optional[TaskStatus] = None


class SortField(str, enum.Enum):
    STATUS = "status"
    ASSIGNEE = "user_id"
    PRIORITY = "priority"
    DUE_DATE = "due_date"


class SortOrder(str, enum.Enum):
    ASC = "ASC"
    DESC = "DESC"


class ListingTaskRequest(BaseModel):
    page: Optional[int] = Query(default=1)
    per_page: Optional[int] = Query(default=5)
    email: Optional[str] = Query(default=None)
    name: Optional[str] = Query(default=None)
    order_by: Optional[SortField] = SortField.DUE_DATE
    order_type: Optional[SortOrder] = SortOrder.ASC
    task_statuses: Optional[List[TaskStatus]] = Query(default=None)
    step_ids: Optional[List[int]] = Query(default=None)


class TriggerTaskAction(str, enum.Enum):
    START = "START"
    SKIPPED = "SKIPPED"


class TriggerTaskRequest(BaseModel):
    action: TriggerTaskAction
    task_ids: List[int]
    schedule_type: Optional[ScheduleType] = None
    custom_datetime: Optional[datetime] = None
    title: Optional[str] = None
    content: Optional[str] = None
    mailbox_id: Optional[int] = None
    mailbox_alias_id: Optional[int] = None
    is_include_opt_out_and_signature: Optional[bool] = False
