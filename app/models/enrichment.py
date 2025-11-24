import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Enum, Integer, String
from sqlmodel import Field, SQLModel, func


class EnrichmentUploadFileMethod(str, enum.Enum):
    OVERWRITE = "OVERWRITE"
    ADD_NEW = "ADD_NEW"


class EnrichmentType(enum.Enum):
    CPN = "CPN"
    PERSON = "PERSON"


class EnrichmentStatus(enum.Enum):
    BEING_IDENTIFIED = "BEING_IDENTIFIED"
    IDENTIFIED = "IDENTIFIED"
    FAILED = "FAILED"


class Enrichment(SQLModel, table=True):
    __tablename__: str = "enrichments"

    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(sa_column=Column(Integer))
    name: str = Field(sa_column=Column(String(255)))
    type: Optional[EnrichmentType] = Field(
        sa_column=Column(
            Enum(EnrichmentType, name="enrichment_type"),
            default=None,
        )
    )
    column_json_mapping: dict = Field(sa_column=Column(JSON))
    status: Optional[EnrichmentStatus] = Field(
        sa_column=Column(
            Enum(EnrichmentStatus, name="enrichment_status"),
            default=None,
        )
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
