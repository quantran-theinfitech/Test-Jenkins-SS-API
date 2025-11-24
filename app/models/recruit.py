from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, Index, SQLModel


class Recruit(SQLModel, table=True):
    __tablename__: str = "recruits"

    __table_args__ = (
        UniqueConstraint("media_code", "media_internal_id", name="recruits_unique_key"),
        Index("idx_recruit_corporate_number", "corporate_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ingest_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    corporate_number: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    media_internal_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(256)), default=None
    )
    source_recruit_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    media_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )

    title: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    sub_title: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    content: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    explain: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    summary: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)

    employment_type_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(20))), default=None
    )
    recruit_tels: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(20))), default=None
    )
    recruit_mails: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    working_address_list: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(2048))), default=None
    )
    working_location: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    working_time: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    application_contacts: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    application_flow: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    recruitment_count: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )

    recruit_sales_approach_reject_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    remote_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    full_remote_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    required_educational_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    required_college_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    required_university_graduate_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    required_post_graduate_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    allow_sidejob_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    online_interview_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )
    attitude_test_flag: Optional[bool] = Field(
        default=None, sa_column=Column(Boolean), nullable=True
    )

    salary_year_min: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_year_max: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_year_value: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_month_min: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_month_max: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_month_value: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_day_min: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_day_max: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_day_value: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_hour_min: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_hour_max: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_hour_value: Optional[int] = Field(
        default=None, sa_column=Column(Integer), nullable=True
    )
    salary_raw: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    welfare_benefit: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    holiday: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)

    tags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    skill_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    recruit_qualifications: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    tech_languages: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    tech_frameworks: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    tech_clouds: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    tech_databases: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    communication_tools: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    management_tools: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    internal_tools: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    crm_tools: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    search_keywords: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )

    large_category: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    medium_category: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    small_category: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    job_company_id: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    other_info: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )

    job_positions: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String(255))), nullable=True
    )
    scores: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String(255))), nullable=True
    )
    job_categories: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String(255))), nullable=True
    )
    job_sub_categories: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String(255))), nullable=True
    )
    start_at: datetime = Field(default=None, sa_column=Column(TIMESTAMP), nullable=True)
    end_at: datetime = Field(default=None, sa_column=Column(TIMESTAMP), nullable=True)

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
