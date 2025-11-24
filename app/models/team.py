import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, String, func
from sqlmodel import Field, SQLModel


class PaidCode(str, enum.Enum):
    FRE = "FRE"
    MICRO = "MICRO"
    SML = "SML"
    STD = "STD"
    PRE = "PRE"
    UNLIMITED = "UNLIMITED"
    CUSTOMIZE = "CUSTOMIZE"


class PlanCode(str, enum.Enum):
    FRE = "FRE"
    MICRO = "MICRO"
    SML = "SML"
    STD = "STD"
    PRE = "PRE"
    UNLIMITED = "UNLIMITED"
    CUSTOMIZE = "CUSTOMIZE"


class Team(SQLModel, table=True):
    __tablename__: str = "teams"
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_plan_code: Optional[PlanCode] = Field(
        default=None, sa_column=Column(Enum(PlanCode), nullable=True)
    )
    form_plan_code: Optional[PlanCode] = Field(
        default=None, sa_column=Column(Enum(PlanCode), nullable=True)
    )
    active_platform: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean, nullable=True)
    )
    integrated_platform: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
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
