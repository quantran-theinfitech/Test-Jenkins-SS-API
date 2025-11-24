import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, Text, func
from sqlmodel import Field, SQLModel


class ReasonCode(str, enum.Enum):
    MONTHLY = "MONTHLY"
    COMPENSATE = "COMPENSATE"
    EXCHANGED = "EXCHANGED"
    ROLLOVER = "ROLLOVER"


class ServiceCode(str, enum.Enum):
    CPN = "CPN"
    PERSON = "PERSON"
    MSG = "MSG"
    CTF = "CTF"
    EMAIL = "EMAIL"
    CSV = "CSV"
    TELESALE = "TELESALE"
    LINKEDIN_CONNECT = "LINKEDIN_CONNECT"
    LINKEDIN_MSG = "LINKEDIN_MSG"
    MAILBOX_CONNECT = "MAILBOX_CONNECT"


class PlanCode(str, enum.Enum):
    FRE = "FRE"
    MICRO = "MICRO"
    SML = "SML"
    STD = "STD"
    PRE = "PRE"
    UNLIMITED = "UNLIMITED"
    CUSTOMIZE = "CUSTOMIZE"


class TeamCredit(SQLModel, table=True):
    __tablename__: str = "team_credits"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    reason_code: Optional[ReasonCode] = Field(
        default=None, sa_column=Column(Enum(ReasonCode), nullable=True)
    )
    service_code: Optional[ServiceCode] = Field(
        default=None, sa_column=Column(Enum(ServiceCode), nullable=True)
    )
    plan_code: Optional[str] = Field(
        nullable=True, sa_column=Column(Enum(PlanCode)), default=None
    )
    amount: int = Field(nullable=False, sa_column=Column(Integer))
    used_amount: int = Field(nullable=False, sa_column=Column(Integer))
    start_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    end_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    is_active: bool = Field(default=True, sa_column=Column(Boolean))
    remarks: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
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
