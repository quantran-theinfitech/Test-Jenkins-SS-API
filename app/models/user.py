import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Enum,
    Index,
    Integer,
    SmallInteger,
    String,
    func,
    text,
)
from sqlmodel import Field, SQLModel


class GenderCode(str, enum.Enum):
    Male = "MALE"
    Female = "FE_MALE"


class RoleCode(str, enum.Enum):
    User = "USER"
    Admin = "ADMIN"


class TeamMemberRoleCode(str, enum.Enum):
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"


class Source(str, enum.Enum):
    ANDIGITAL_FORM = "ANDIGITAL_FORM"
    DIRECTLY_REGISTER = "DIRECTLY_REGISTER"


class User(SQLModel, table=True):
    __tablename__: str = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    role_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    team_member_role_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    email: str = Field(nullable=False, sa_column=Column(String(255)), default=None)
    password: str = Field(nullable=True, sa_column=Column(String(255)), default=None)
    initial_password: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    email_verified_at: datetime = Field(nullable=True, default=None)
    gender_code: Optional[GenderCode]
    linkedin_profile_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    company_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    department_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    tel: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    expect_meeting_flag: Optional[int] = Field(
        nullable=True, sa_column=Column(SmallInteger), default=None
    )
    position_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    flag_first_login: bool = Field(
        sa_column=Column(Boolean, nullable=False), default=True
    )
    show_tutorial_flag: bool = Field(
        sa_column=Column(Boolean, nullable=False), default=True
    )
    source: Optional[Source] = Field(
        default=None, sa_column=Column(Enum(Source), nullable=True)
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
    avatar_path: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    password_updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    reset_password_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP, nullable=True)
    )
    __table_args__ = (
        Index(
            "unique_active_email",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
