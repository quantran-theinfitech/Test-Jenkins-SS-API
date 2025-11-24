from datetime import datetime
from typing import Optional

from sqlmodel import TIMESTAMP, Column, Field, Integer, SQLModel, String, func


class TeamInvitation(SQLModel, table=True):
    __tablename__: str = "team_invitations"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    inviter_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    role: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    token: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    accepted_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP, server_default=None)
    )
    rejected_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP, server_default=None)
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
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    deleted_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
