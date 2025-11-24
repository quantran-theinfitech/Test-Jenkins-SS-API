from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Text, func
from sqlmodel import Field, SQLModel, UniqueConstraint


class Relocation(SQLModel, table=True):
    __tablename__: str = "relocations"
    __table_args__ = (
        UniqueConstraint("media_internal_id", name="relocations_unique_id"),
    )
    media_internal_id: Optional[str] = Field(sa_column=Column(Text, primary_key=True))
    media_code: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    source_relocation_url: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    corporate_number: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    article_id: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    name: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    name_hepburn: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    old_position: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    new_position: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    company_name: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    company_name_hepburn: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    published_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP, server_default=func.now(), onupdate=func.now()),
    )
