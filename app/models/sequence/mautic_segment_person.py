from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, func
from sqlmodel import Field, SQLModel


class SequenceMauticSegmentPerson(SQLModel, table=True):
    __tablename__: str = "sequence_mautic_segment_persons"
    id: Optional[int] = Field(default=None, primary_key=True)
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
    mautic_segment_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    external_mautic_segment_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_person_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    external_mautic_person_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
