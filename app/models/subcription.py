from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, func
from sqlmodel import Field, SQLModel

from app.models.plan import PlanServiceCode
from app.models.team import PlanCode


class Subcription(SQLModel, table=True):
    __tablename__: str = "subcriptions"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    plan_code: Optional[str] = Field(
        nullable=True, sa_column=Column(Enum(PlanCode)), default=None
    )
    service_code: Optional[PlanServiceCode] = Field(
        default=None, sa_column=Column(Enum(PlanServiceCode), nullable=True)
    )
    start_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    expire_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    is_active: bool = Field(default=True, sa_column=Column(Boolean))
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    created_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    deleted_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
