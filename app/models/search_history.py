import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, Text, func
from sqlmodel import Field, SQLModel


class SEARCH_HISTORY_ENUM(str, enum.Enum):
    PERSON = "PERSON"
    COMPANY = "COMPANY"


class SearchHistory(SQLModel, table=True):
    __tablename__: str = "search_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    type: Optional[SEARCH_HISTORY_ENUM] = Field(
        nullable=True, sa_column=Column(Enum(SEARCH_HISTORY_ENUM)), default=None
    )
    prompt_message: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    user_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
