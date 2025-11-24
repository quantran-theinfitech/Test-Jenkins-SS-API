from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Float,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, SQLModel


class CompanyCustom(SQLModel, table=True):
    __tablename__: str = "companies_custom"

    __table_args__ = (
        UniqueConstraint("company_custom_id", name="companies_custom_id_unique"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_custom_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    establish_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    establish_time_level: Optional[str] = Field(nullable=True, default=None)
    name: Optional[str] = Field(nullable=True, default=None)
    kana_name: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    english_name: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    normalized_name: Optional[str] = Field(
        default=None, sa_column=Column(Text, index=True), nullable=True
    )
    postal_code: Optional[int] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    nta_city_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    nta_prefecture_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    address: Optional[str] = Field(nullable=True, default=None)
    corporate_number: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    corporate_kind: Optional[int] = Field(
        nullable=True, sa_column=Column(SmallInteger), default=None
    )
    nta_closed_date: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    nta_closed_reason: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    nta_updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    nta_created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    hp_url: Optional[str] = Field(nullable=True, default=None)
    domain: Optional[str] = Field(nullable=True, default=None)
    president_name: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    president_dob: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    factories_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    branches_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    headquarters_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    industry_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    business_content: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    listing_market_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    listing_year: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    listing_time_code: Optional[str] = Field(nullable=True, default=None)
    revenue_change: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    employee_change: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    revenue_change_rate: float = Field(
        nullable=True, sa_column=Column(Float), default=None
    )
    youtube_url: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    twitter_url: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    facebook_url: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    contact_form_url: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    president_university: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    revenue: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    recruit_phone: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    sub_companies_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    phone: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    recruit_email: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    contact_email: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    capital_adequacy_ratio: float = Field(
        nullable=True, sa_column=Column(Float), default=None
    )
    capital: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    capital_change: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    average_work_duration: float = Field(
        nullable=True, sa_column=Column(Float), default=None
    )
    fax: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    closing_month: Optional[int] = Field(
        nullable=True, sa_column=Column(SmallInteger), default=None
    )
    employee_change_rate: float = Field(
        nullable=True, sa_column=Column(Float), default=None
    )
    employees_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    average_age: float = Field(nullable=True, sa_column=Column(Float), default=None)
    average_salary: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    latest_recruits_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    this_month_recruits_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    this_month_doda_recruits_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    this_month_mynavi_tenshoku_recruits_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    latest_press_release_at: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    this_month_prtimes_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    this_month_value_press_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    display_flag: Optional[int] = Field(
        nullable=True, sa_column=Column(SmallInteger), default=None
    )
    meta_title: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    meta_description: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    meta_keywords: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    main_sub_industry_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    sub_industries_code: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    revenue_raw: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    capital_raw: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    tool_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    one_month_employee_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    three_month_employee_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    six_month_employee_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    one_year_employee_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    one_month_capital_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    three_month_capital_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    six_month_capital_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    one_year_capital_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    one_month_revenue_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    three_month_revenue_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    six_month_revenue_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    one_year_revenue_delta: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    latest_new_graduate_recruit_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    press_release_media_codes: Optional[str] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    recruit_media_codes: Optional[str] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    occupation_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    raw_occupations: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    skill_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    group_employee_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    main_customers: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    # history
    group_companies: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    market_capitalization_raw: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    market_capitalization: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    address_latitude: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    address_longitude: Optional[int] = Field(
        nullable=True, sa_column=Column(BigInteger), default=None
    )
    recruit_tags: Optional[List[str]] = Field(
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
    business_model_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(10))), default=None
    )
    display_ng_flag: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    contact_ng_flag: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    contact_info_ng_flag: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    contact_sales_ng_flag: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    three_month_funding_flags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    six_month_funding_flags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    twelve_month_funding_flags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    all_funding_flags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
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
