from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field

from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.models.team_company import StatusCode


class CompanyBase(BaseModel):
    id: Optional[int]
    establish_at: Optional[datetime] = None
    establish_time_level: Optional[str] = None
    name: Optional[str] = None
    kana_name: Optional[str] = None
    english_name: Optional[str] = None
    postal_code: Optional[int] = None
    nta_city_id: Optional[int] = None
    nta_prefecture_id: Optional[int] = None
    address: Optional[str] = None
    corporate_number: Optional[str] = None
    corporate_kind: Optional[int] = None
    nta_closed_date: Optional[datetime] = None
    nta_closed_reason: Optional[str] = None
    nta_updated_at: Optional[datetime] = None
    nta_created_at: Optional[datetime] = None
    hp_url: Optional[str] = None
    domain: Optional[str] = None
    president_name: Optional[str] = None
    president_dob: Optional[datetime] = None
    factories_count: Optional[int] = None
    branches_count: Optional[int] = None
    headquarters_count: Optional[int] = None
    industry_code: Optional[str] = None
    sub_industries_code: Optional[List[str]] = None
    business_content: Optional[str] = None
    listing_market_code: Optional[str] = None
    listing_year: Optional[int] = None
    listing_time_code: Optional[str] = None
    revenue_change: Optional[int] = None
    employee_change: Optional[int] = None
    revenue_change_rate: Optional[float] = None
    revenue_raw: Optional[str] = None
    revenue_ai: Optional[int] = None
    youtube_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    wantedly_url: Optional[str] = None
    youtrust_url: Optional[str] = None
    facebook_url: Optional[str] = None
    contact_form_url: Optional[str] = None
    president_university: Optional[str] = None
    revenue: Optional[int] = None
    recruit_phone: Optional[str] = None
    sub_companies_count: Optional[int] = None
    phone: Optional[str] = None
    recruit_email: Optional[str] = None
    contact_email: Optional[str] = None
    capital_adequacy_ratio: Optional[float] = None
    capital: Optional[int] = None
    capital_change: Optional[int] = None
    average_work_duration: Optional[float] = None
    fax: Optional[str] = None
    closing_month: Optional[int] = None
    employee_change_rate: Optional[float] = None
    employees_count: Optional[int] = None
    average_age: Optional[float] = None
    average_salary: Optional[int] = None
    latest_recruits_at: Optional[datetime] = None
    this_month_recruits_count: Optional[int] = None
    this_month_mynavi_tenshoku_recruits_count: Optional[int] = None
    latest_press_release_at: Optional[int] = None
    this_month_prtimes_count: Optional[int] = None
    this_month_value_press_count: Optional[int] = None
    display_flag: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    business_model_codes: Optional[List[str]] = None
    press_release_media_codes: Optional[List[str]] = None
    recruit_media_codes: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    favicon_url: Optional[str] = None


class TeamCompany(CompanyBase):
    tags: Optional[List[str]] = None
    status_code: Optional[StatusCode] = None
    sales_log_count: Optional[int] = None
    company_custom_id: Optional[str] = None


class DownloadCompanyRequest(BaseModel):
    corporate_numbers: List[str] = Field(...)


class DownloadCompanyResponse(CompanyBase):
    downloaded_flag: bool = True


class SaveSearchConditionRequest(BaseModel):
    name: str
    conditions: SearchCrossRequest


class UpdateTeamCompanyRequest(BaseModel):
    status_code: Optional[StatusCode]
    tags: Optional[List[str]]


class UpdateTeamCompanyResponse(BaseModel):
    status_code: Optional[StatusCode] = None
    tags: Optional[List[str]] = None


class GetCollectionCompanyResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[TeamCompany]
    main_person_id: Optional[int]


class CompanyDetailResponse(CompanyBase):
    status_code: Optional[StatusCode] = None
    tags: Optional[List[str]]
    downloaded_flag: Optional[bool] = None
    available_fields: Optional[List[str]] = []
    favicon_url: Optional[str]


class CompanyDetailStatisticData(BaseModel):
    recruits_total: Optional[int] = None
    press_releases_total: Optional[int] = None
    events_total: Optional[int] = None
    employees_total: Optional[int] = None
    services_total: Optional[int] = None
    technologies_total: Optional[int] = None
    investor_relations_total: Optional[int] = None


class CompanyDetailStatisticTotalResponse(BaseModel):
    data: CompanyDetailStatisticData


class GetCompanyActivitesRequest(BaseModel):
    corporate_number: str
    page: int = 1
    per_page: int = 10


class CompanyActivityType(Enum):
    PRESS_RELEASE = "PRESS_RELEASE"
    RECRUITMENT = "RECRUITMENT"
    EVENT = "EVENT"


class CompanyActivitiesItem(BaseModel):
    title: Optional[str]
    content: Optional[str]
    activity_type: CompanyActivityType
    media_code: Optional[str]
    source_url: Optional[str]
    posted_at: Optional[datetime]


class CompanyActivitiesResponse(BaseModel):
    data: List[CompanyActivitiesItem]


class CompanyTechnologyBase(BaseModel):
    name: Optional[str]
    icon: Optional[str]
    website: Optional[str]


class CompanyTechnologyItem(BaseModel):
    category_name: Optional[str] = None
    technology: List[CompanyTechnologyBase]


class CompanyTechnologyResponse(BaseModel):
    data: List[CompanyTechnologyItem]


class CompanyByKeyword(BaseModel):
    name: Optional[str] = None
    corporate_number: Optional[str] = None
    domain: Optional[str] = None
    hp_url: Optional[str] = None
    downloaded_flag: Optional[bool] = None
    favicon_url: Optional[str] = None
    president_name: Optional[str] = None


class CompanyByKeywordResponse(BaseModel):
    data: List[CompanyByKeyword]


class ListingCompanyStatisticResponse(BaseModel):
    total: int
    unlimited_total: int
    phone: int
    contact_email: int
    recruit_phone: int
    recruit_email: int
    contact_form_url: int
    hp_url: int


class DownloadCompanyMode(Enum):
    RANDOM = "RANDOM"
    EXACT = "EXACT"


class DownloadCompanyConditionRequest(BaseModel):
    search_condition: SearchCrossRequest
    mode: DownloadCompanyMode


class CompanyFormJobResponse(BaseModel):
    name: Optional[str] = None
    corporate_number: Optional[str] = None
    president_name: Optional[str] = None
    phone: Optional[str] = None
    industry_code: Optional[str] = None
    listing_market_code: Optional[str] = None
    tags: Optional[List[str]] = None


class FilterWappalyzer(Enum):
    MANAGEMENT_TOOLS = "management_tools"
    COMMUNICATION_TOOLS = "communication_tools"
    LANGUAGE_TECHNOLOGIES = "tech_languages"
    FRAMEWORK_TECHNOLOGIES = "tech_frameworks"
    CLOUD_SERVICES = "tech_clouds"
    MARKETING_TOOLS = "crm_tools"
    OTHER_TOOLS = "internal_tools"
