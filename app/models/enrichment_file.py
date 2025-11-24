import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String
from sqlmodel import Field, SQLModel, func


class EnrichmentFileEncoding(enum.Enum):
    UTF_8 = "UTF_8"
    SHIFT_JIS = "SHIFT_JIS"


class EnrichmentFileDelimiter(enum.Enum):
    COMMA = "COMMA"
    TAB = "TAB"


class EnrichmentFile(SQLModel, table=True):
    __tablename__: str = "enrichment_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    enrichment_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    file_name: str = Field(sa_column=Column(String(255)))
    s3_object_key: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    encoding: Optional[EnrichmentFileEncoding] = Field(
        sa_column=Column(
            Enum(EnrichmentFileEncoding, name="enrichment_file_encoding"),
            default=None,
        )
    )
    delimiter: Optional[EnrichmentFileDelimiter] = Field(
        sa_column=Column(
            Enum(EnrichmentFileDelimiter, name="enrichment_file_delimiter"),
            default=None,
        )
    )
    upload_process_status: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
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
