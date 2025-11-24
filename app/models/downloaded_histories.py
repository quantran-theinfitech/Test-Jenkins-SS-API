from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, func
from sqlmodel import Field, SQLModel

from .team_credit import ServiceCode


class DownloadedHistory(SQLModel, table=True):
    __tablename__: str = "downloaded_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    amount: int = Field(nullable=False, sa_column=Column(Integer))
    service_code: Optional[ServiceCode] = Field(
        default=None, sa_column=Column(Enum(ServiceCode), nullable=True)
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
