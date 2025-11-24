from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel


class EsCompanyBase(BaseModel):
    establish_at: Optional[datetime]
    establish_time_level: Optional[Union[str, None]]
    name: Optional[Union[str, None]]
    kana_name: Optional[Union[str, None]]
    english_name: Optional[Union[str, None]]
    postal_code: Optional[Union[str, None]]
    nta_city_id: Optional[int]
    nta_prefecture_id: Optional[int]
    address: Optional[Union[str, None]]
    corporate_number: str
    corporate_kind: Optional[int]
    nta_closed_Date: Optional[datetime]
    nta_closed_reason: Optional[Union[str, None]]
    nta_updated_at: Optional[datetime]
    nta_created_at: Optional[datetime]
    hp_url: Optional[Union[str, None]]
    president_name: Optional[Union[str, None]]
    president_dob: Optional[datetime]
    factories_count: Optional[int]
    branches_count: Optional[int]
    headquarters_count: Optional[int]
    industry_code: Optional[Union[str, None]]
    main_sub_industry_code: Optional[Union[str, None]]
    sub_industries_code: Optional[List[Union[str, None]]]
    business_content: Optional[Union[str, None]]
    listing_market_code: Optional[Union[str, None]]
    listing_year: Optional[int]
    listing_time_code: Optional[Union[str, None]]
    revenue_change: Optional[int]
    employee_change: Optional[int]
    revenue_change_rate: Optional[float]
    youtube_url: Optional[Union[str, None]]
    twitter_url: Optional[Union[str, None]]
    facebook_url: Optional[Union[str, None]]
    contact_form_url: Optional[Union[str, None]]
    president_university: Optional[Union[str, None]]
    revenue: Optional[int]
    revenue_raw: Optional[Union[str, None]]
    recruit_phone: Optional[Union[str, None]]
    sub_companies_count: Optional[int]
    phone: Optional[Union[str, None]]
    recruit_email: Optional[Union[str, None]]
    contact_email: Optional[Union[str, None]]
    capital_adequacy_ratio: Optional[float]
    capital: Optional[int]
    capital_raw: Optional[Union[str, None]]
    capital_change: Optional[int]
    average_work_duration: Optional[float]
    fax: Optional[Union[str, None]]
    closing_month: Optional[int]
    employee_change_rate: Optional[float]
    employees_count: Optional[int]
    average_age: Optional[float]
    average_salary: Optional[int]
    latest_recruits_at: Optional[datetime]
    this_month_recruits_count: Optional[int]
    this_month_doda_recruits_count: Optional[int]
    this_month_mynavi_tenshoku_recruits_count: Optional[int]
    latest_press_release_at: Optional[datetime]
    this_month_prtimes_count: Optional[int]
    this_month_value_press_count: Optional[int]
    display_flag: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    meta_title: Optional[Union[str, None]]
    meta_description: Optional[Union[str, None]]
    meta_keywords: Optional[Union[str, None]]
    raw_industries: Optional[List[Union[str, None]]]
    press_release_media_codes: Optional[List[Union[str, None]]]
    tool_codes: Optional[List[Union[str, None]]]
    one_month_employee_delta: Optional[int]
    three_month_employee_delta: Optional[int]
    six_month_employee_delta: Optional[int]
    one_year_employee_delta: Optional[int]
    one_month_capital_delta: Optional[int]
    three_month_capital_delta: Optional[int]
    six_month_capital_delta: Optional[int]
    one_year_capital_delta: Optional[int]
    one_month_revenue_delta: Optional[int]
    three_month_revenue_delta: Optional[int]
    six_month_revenue_delta: Optional[int]
    one_year_revenue_delta: Optional[int]
    recruit_media_codes: Optional[List[Union[str, None]]]
    latest_new_graduate_recruit_at: Optional[datetime]
    latest_middle_recruit_at: Optional[datetime]
    latest_parttime_recruit_at: Optional[datetime]
    employment_type_codes: Optional[List[Union[str, None]]]
    recruit_features: Optional[List[Union[str, None]]]
    occupation_codes: Optional[List[Union[str, None]]]
    raw_occupations: Optional[List[Union[str, None]]]
    skill_codes: Optional[List[Union[str, None]]]
    group_employee_count: Optional[int]
    main_customers: Optional[Union[str, None]]
    group_companies: Optional[Union[str, None]]
    market_capitalization_raw: Optional[Union[str, None]]
    market_capitalization: Optional[int]
    address_latitude: Optional[int]
    address_longitude: Optional[int]
    recruit_tags: Optional[List[Union[str, None]]]
    recruit_qualifications: Optional[List[Union[str, None]]]
    tech_languages: Optional[List[Union[str, None]]]
    tech_frameworks: Optional[List[Union[str, None]]]
    tech_clouds: Optional[List[Union[str, None]]]
    tech_databases: Optional[List[Union[str, None]]]
    communication_tools: Optional[List[Union[str, None]]]
    management_tools: Optional[List[Union[str, None]]]
    internal_tools: Optional[List[Union[str, None]]]
    crm_tools: Optional[List[Union[str, None]]]
    business_model_codes: Optional[List[Literal["B2B", "B2C"]]]


class EsCompanyWithTags(EsCompanyBase):
    tags: Optional[List[str]]


class SearchCompanyItem(EsCompanyBase):
    id: Optional[int]
    downloaded_flag: bool
    available_fields: Optional[List[str]]
    original_tags: Optional[List[str]]
    favicon_url: Optional[str]


class SearchCompanyResponse(BaseModel):
    page: int
    per_page: int
    total: int
    unlimited_total: int
    data: List[SearchCompanyItem]


class SearchCompanyByTeamIdItem(EsCompanyBase):
    id: Optional[int]


class SearchCompanyByTeamIdResponse(BaseModel):
    page: int
    per_page: int
    total: int
    unlimited_total: int
    data: List[SearchCompanyByTeamIdItem]


class GetListCorporateNumbers(BaseModel):
    corporate_numbers: List[str]


class GetTotalCompanyLockAndUnlockResponse(BaseModel):
    total_lock: int
    total_unlock: int
    total: int
    total_push_companies: Optional[int] = None
