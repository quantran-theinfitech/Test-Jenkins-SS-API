import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Column, Enum, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class StatusCode(str, enum.Enum):
    PENDING = "PENDING"
    APPROACH_NG = "APPROACH_NG"
    APO_WON = "APO_WON"
    APO_EXPECTED = "APO_EXPECTED"
    RECALL = "RECALL"


class TeamCompany(SQLModel, table=True):
    __tablename__: str = "team_companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    corporate_number: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    status_code: Optional[StatusCode] = Field(
        default=None, sa_column=Column(Enum(StatusCode), nullable=True)
    )
    tags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    sent_contact_form_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
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
