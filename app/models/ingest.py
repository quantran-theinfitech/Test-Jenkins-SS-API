import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class StateCode(str, enum.Enum):
    OLD = "OLD"
    NEW = "NEW"
    IN_DB = "IN_DB"
    PROCESSING = "PROCESSING"
    DONE = "DONE"


class Ingest(SQLModel, table=True):
    __tablename__: str = "ingests"
    __table_args__ = (UniqueConstraint("ingest_id", name="ingest_unique_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    ingest_id: str = Field(nullable=False, sa_column=Column(String(255)), unique=True)
    state: Optional[StateCode] = Field(
        default=StateCode.NEW, sa_column=Column(Enum(StateCode), nullable=True)
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
