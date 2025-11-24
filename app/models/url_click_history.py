import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String, func
from sqlmodel import Field, SQLModel


class TemplateTypeCode(str, enum.Enum):
    FORM = "FORM"
    MAIL = "MAIL"
    MSG = "MSG"


class UrlClickHistory(SQLModel, table=True):
    __tablename__: str = "url_click_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    tracking_url_id: int = Field(sa_column=Column(Integer, nullable=False))
    corporate_number: str = Field(sa_column=Column(String, nullable=False))
    template_type_code: Optional[TemplateTypeCode] = Field(
        nullable=True, sa_column=Column(Enum(TemplateTypeCode)), default=None
    )
    template_id: Optional[int] = Field(
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
