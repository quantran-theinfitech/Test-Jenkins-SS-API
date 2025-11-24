from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel

from .search_press_releases import SearchPressReleaseRequest
from .search_recruits import AnnualIncome, SearchRecruitRequest


class TypeDownload(str, Enum):
    CREDIT = "CREDIT"
    DOWNLOADED = "DOWNLOADED"


class ContactInformation(BaseModel):
    operator: Optional[Literal["AND", "OR"]]
    contact_info: Optional[List[str]]


class DurationFunding(str, Enum):
    THREE_MONTH = "THREE_MONTH"
    SIX_MONTH = "SIX_MONTH"
    ONE_YEAR = "ONE_YEAR"


class FundingStage(str, Enum):
    SEED_ROUND = "SEED_ROUND"
    ANGEL_ROUND = "ANGEL_ROUND"
    VENTURE_ROUND = "VENTURE_ROUND"
    SERIES_A = "SERIES_A"
    SERIES_B = "SERIES_B"
    SERIES_C = "SERIES_C"
    SERIES_D = "SERIES_D"
    SERIES_E = "SERIES_E"
    SERIES_F = "SERIES_F"
    DEBT_FINANCING = "DEBT_FINANCING"
    EQUITY_CROWDFUNDING = "EQUITY_CROWDFUNDING"
    CONVERTIBLE_NOTE = "CONVERTIBLE_NOTE"
    PRIVATE_EQUITY = "PRIVATE_EQUITY"


class SortField(str, Enum):
    EMPLOYEES_COUNT = "EMPLOYEES_COUNT"
    REVENUE = "REVENUE"
    CAPITAL = "CAPITAL"


class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class Sorting(BaseModel):
    field: Optional[SortField] = SortField.EMPLOYEES_COUNT
    order: Optional[SortOrder] = SortOrder.DESC


class CompanyIndustry(BaseModel):
    large_industries: Optional[List[str]]
    sub_industries: Optional[List[str]]


class Keyword(BaseModel):
    and_keywords: Optional[List[str]]
    or_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]
    is_exact: Optional[bool]


class KeywordSearch(BaseModel):
    or_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]


class PostingPeriod(str, Enum):
    ONE_MONTH = "ONE_MONTH"
    ONE_TO_THREE_MONTH = "ONE_TO_THREE_MONTH"
    THREE_TO_SIX_MONTH = "THREE_TO_SIX_MONTH"
    SIX_TO_ONE_YEAR = "SIX_TO_ONE_YEAR"
    ONE_YEAR_OR_MORE = "ONE_YEAR_OR_MORE"


class MediaCode(str, Enum):
    ATPRESS = "ATPRESS"
    BIZREACH = "BIZREACH"
    DODA = "DODA"
    GREEN = "GREEN"
    HELLOWORK = "HELLOWORK"
    MYNAVI_SHINSOTSU = "MYNAVI_SHINSOTSU"
    MYNAVI_TENSHOKU = "MYNAVI_TENSHOKU"
    RIKUNABI = "RIKUNABI"
    RIKUNABI_SHINSOTSU = "RIKUNABI_SHINSOTSU"
    TYPE = "TYPE"
    WANTEDLY = "WANTEDLY"
    PRTIMES = "PRTIMES"
    VALUEPRESS = "VALUEPRESS"
    OPENWORK = "OPENWORK"
    EAIDEM = "EAIDEM"
    HERP= "HERP"
    DAIJOB = "DAIJOB"
    WORKPORT = "WORKPORT"


class PressRelease(BaseModel):
    posting_period: Optional[List[PostingPeriod]] = None
    media: Optional[List[MediaCode]] = None
    keyword: Optional[Keyword] = None


class EstablishAt(BaseModel):
    exclude_unknown_flag: Optional[bool]
    start_date: Optional[datetime]
    end_date: Optional[datetime]


class ClosingMonth(BaseModel):
    exclude_unknown_flag: Optional[bool]
    months: Optional[List[int]]


class ListingDivision(BaseModel):
    exclude_unknown_flag: Optional[bool]
    listed: Optional[bool]
    unlisted: Optional[bool]


class NumberRangeWithoutFlag(BaseModel):
    gte: Optional[int]
    lte: Optional[int]


class SearchMode(str, Enum):
    EXACT = "EXACT"
    FUZZY = "FUZZY"


class NumberRangeWithFlag(BaseModel):
    exclude_unknown_flag: Optional[bool]
    ranges: Optional[List[NumberRangeWithoutFlag]]


class JobCategory(BaseModel):
    halfway: Optional[List[str]]
    new_graduate: Optional[List[str]]
    part_time: Optional[List[str]]


class PublicationMedia(BaseModel):
    mid_careers: Optional[List[str]]
    new_graduates: Optional[List[str]]


class BusinessModel(BaseModel):
    exclude_unknown_flag: Optional[bool]
    business_model_codes: Optional[List[Literal["B2B", "B2C"]]]


class DateRange(BaseModel):
    start_date: Optional[datetime]
    end_date: Optional[datetime]


class JobUpdateDate(BaseModel):
    halfway: Optional[DateRange]
    new_graduate: Optional[DateRange]
    part_time: Optional[DateRange]


class FeatureFlag(BaseModel):
    operator: Optional[Literal["AND", "OR"]]
    job_remote_flag: Optional[bool]
    job_full_remote_flag: Optional[bool]
    job_required_educational_flag: Optional[bool]
    job_required_college_flag: Optional[bool]
    job_required_university_graduation_flag: Optional[bool]
    job_required_post_graduate_flag: Optional[bool]
    job_allow_sidejob_flag: Optional[bool]


class EmploymentType(BaseModel):
    operator: Optional[Literal["AND", "OR"]]
    employment_types: Optional[List[str]]


class Salary(BaseModel):
    exclude_unknown_flag: Optional[bool]
    type: Optional[Literal["MONTH", "DAY", "HOUR"]] = "HOUR"
    gte: Optional[int]
    lte: Optional[int]


class SalaryKeyword(Keyword):
    exclude_unknown_flag: Optional[bool]


class CollectionList(BaseModel):
    or_collections: Optional[List[int]]
    exclude_collections: Optional[List[int]]


class CorporateNumberByCollection(BaseModel):
    or_corporate_numbers: Optional[List[str]]
    exclude_corporate_numbers: Optional[List[str]]


class ListCorporateNumber(BaseModel):
    corporate_numbers: Optional[List[str]] = []


class CompanyIdentified(BaseModel):
    enrichment_ids: Optional[List[int]] = None


class CorporateNumberByIdentified(BaseModel):
    or_corporate_numbers: Optional[List[str]]


class UuidsByCollection(BaseModel):
    or_uuids: Optional[List[str]]
    exclude_uuids: Optional[List[str]]


class Capital(BaseModel):
    exclude_unknown_flag: Optional[bool]
    ranges: Optional[List[NumberRangeWithoutFlag]]


class Revenue(BaseModel):
    exclude_unknown_flag: Optional[bool]
    ranges: Optional[List[NumberRangeWithoutFlag]]


class Location(BaseModel):
    prefectures: Optional[List[int]]
    cities: Optional[List[int]]


class Platform(BaseModel):
    platforms: Optional[List[str]]
    operator: Optional[Literal["AND", "OR"]] = "OR"


class Funding(BaseModel):
    duration: Optional[DurationFunding]
    funding_stage: Optional[List[FundingStage]]


class SearchCompanyRequest(BaseModel):
    company_keywords: Optional[Keyword] = None
    industries: Optional[CompanyIndustry] = None
    industry_keywords: Optional[Keyword] = None
    locations: Optional[Location] = None
    location_keywords: Optional[Keyword] = None
    business_content: Optional[Keyword] = None
    corporate_numbers: Optional[List[str]] = None
    exclude_corporate_numbers: Optional[List[str]] = None
    company_name: Optional[str] = None
    domain_name: Optional[str] = None
    date_of_establishment: Optional[EstablishAt] = None
    closing_month: Optional[ClosingMonth] = None
    listing_division: Optional[ListingDivision] = None
    listed_exchanges: Optional[List[str]] = None
    factories_count: Optional[NumberRangeWithoutFlag] = None
    listing_year: Optional[NumberRangeWithoutFlag] = None
    average_salary: Optional[NumberRangeWithoutFlag] = None
    average_age: Optional[List[NumberRangeWithoutFlag]] = None
    average_work_duration: Optional[NumberRangeWithoutFlag] = None
    press_release: Optional[KeywordSearch] = None
    marketing_tools: Optional[KeywordSearch] = None
    communication_tools: Optional[KeywordSearch] = None
    management_tools: Optional[KeywordSearch] = None
    other_tools: Optional[KeywordSearch] = None
    number_of_employees: Optional[NumberRangeWithFlag] = None
    capital: Optional[Capital] = None
    revenue: Optional[Revenue] = None
    language_technologies: Optional[KeywordSearch] = None
    framework_technologies: Optional[KeywordSearch] = None
    cloud_services: Optional[KeywordSearch] = None
    publication_media: Optional[PublicationMedia] = None
    contact_information: Optional[ContactInformation] = None
    business_models: Optional[BusinessModel] = None
    job_category: Optional[JobCategory] = None
    job_update_date: Optional[JobUpdateDate] = None
    feature_flag: Optional[FeatureFlag] = None
    employment_type: Optional[EmploymentType] = None
    occupation_codes: Optional[List[str]] = None
    occupation_keywords: Optional[Keyword] = None
    job_skill_codes: Optional[List[str]] = None
    job_skill_code_keywords: Optional[Keyword] = None
    job_locations: Optional[Location] = None
    job_location_keywords: Optional[Keyword] = None
    job_keywords: Optional[Keyword] = None
    job_salary: Optional[Salary] = None
    job_salary_keywords: Optional[SalaryKeyword] = None
    job_annual_income: Optional[AnnualIncome] = None
    tags: Optional[List[str]] = None
    original_tags: Optional[List[str]] = None
    is_companies_unlocked: Optional[bool] = None
    company_collections: Optional[CollectionList] = None
    corporate_numbers_by_collection: Optional[CorporateNumberByCollection] = None
    funding: Optional[Funding] = None
    mode: Optional[SearchMode] = None
    sorting: Optional[Sorting] = None
    companies_identified: Optional[CompanyIdentified] = None
    corporate_numbers_identified: Optional[CorporateNumberByIdentified] = None

    class Config:
        extra = "allow"


class SearchPersonRequest(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    platform: Optional[Platform] = None
    person_keywords: Optional[Keyword] = None
    role_codes: Optional[List[str]] = None
    role_group_codes: Optional[List[str]] = None
    sns_url: Optional[str] = None
    person_uuids: Optional[List[str]] = None
    is_persons_unlocked: Optional[bool] = None
    person_collections: Optional[CollectionList] = None
    uuids_by_collection: Optional[UuidsByCollection] = None

    class Config:
        extra = "allow"


class CompanyColumnSettings(BaseModel):
    column: str
    visible: bool
    isPinned: bool


class SearchCrossRequest(
    SearchCompanyRequest,
    SearchPersonRequest,
    SearchRecruitRequest,
):
    keyword: Optional[str] = None
    column_settings: Optional[Dict[str, CompanyColumnSettings]] = None
    is_default_filter: Optional[bool] = None
    new_press_release: Optional[SearchPressReleaseRequest] = None
    recruit: Optional[SearchRecruitRequest] = None
    cache_key: Optional[str] = None

    class Config:
        extra = "allow"


class DowloadCsvRequest(SearchCrossRequest):
    list_company_corporate_numbers: Optional[List[str]] = None
    list_person_uuids: Optional[List[str]] = None
    type_download: Optional[TypeDownload]


class GetIDsByTotalSelect(BaseModel):
    total_select: Optional[int] = None
    max_person_by_company: Optional[int] = None


class ListUUIDs(BaseModel):
    uuids: Optional[List[str]] = []


class EsCompanyBase(BaseModel):
    establish_at: Optional[datetime]
    establish_time_level: Optional[str]
    name: Optional[str]
    kana_name: Optional[str]
    english_name: Optional[str]
    postal_code: Optional[str]
    nta_city_id: Optional[int]
    nta_prefecture_id: Optional[int]
    address: Optional[str]
    corporate_number: str
    corporate_kind: Optional[int]
    nta_closed_Date: Optional[datetime]
    nta_closed_reason: Optional[str]
    nta_updated_at: Optional[datetime]
    nta_created_at: Optional[datetime]
    hp_url: Optional[str]
    president_name: Optional[str]
    president_dob: Optional[datetime]
    factories_count: Optional[int]
    branches_count: Optional[int]
    headquarters_count: Optional[int]
    industry_code: Optional[str]
    main_sub_industry_code: Optional[str]
    sub_industries_code: Optional[List[str]]
    business_content: Optional[str]
    listing_market_code: Optional[str]
    listing_year: Optional[int]
    listing_time_code: Optional[str]
    revenue_change: Optional[int]
    employee_change: Optional[int]
    revenue_change_rate: Optional[float]
    youtube_url: Optional[str]
    twitter_url: Optional[str]
    facebook_url: Optional[str]
    contact_form_url: Optional[str]
    president_university: Optional[str]
    revenue: Optional[int]
    revenue_raw: Optional[str]
    recruit_phone: Optional[str]
    sub_companies_count: Optional[int]
    phone: Optional[str]
    recruit_email: Optional[str]
    contact_email: Optional[str]
    capital_adequacy_ratio: Optional[float]
    capital: Optional[int]
    capital_raw: Optional[str]
    capital_change: Optional[int]
    average_work_duration: Optional[float]
    fax: Optional[str]
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
    meta_title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    raw_industries: Optional[List[Union[str, None]]]
    press_release_media_codes: Optional[List[str]]
    tool_codes: Optional[List[str]]
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
    recruit_media_codes: Optional[List[str]]
    latest_new_graduate_recruit_at: Optional[datetime]
    latest_middle_recruit_at: Optional[datetime]
    latest_parttime_recruit_at: Optional[datetime]
    employment_type_codes: Optional[List[str]]
    recruit_features: Optional[List[str]]
    occupation_codes: Optional[List[str]]
    raw_occupations: Optional[List[str]]
    skill_codes: Optional[List[str]]
    group_employee_count: Optional[int]
    main_customers: Optional[str]
    group_companies: Optional[str]
    market_capitalization_raw: Optional[str]
    market_capitalization: Optional[int]
    address_latitude: Optional[int]
    address_longitude: Optional[int]
    recruit_tags: Optional[List[str]]
    recruit_qualifications: Optional[List[str]]
    tech_languages: Optional[List[str]]
    tech_frameworks: Optional[List[str]]
    tech_clouds: Optional[List[str]]
    tech_databases: Optional[List[str]]
    communication_tools: Optional[List[str]]
    management_tools: Optional[List[str]]
    internal_tools: Optional[List[str]]
    crm_tools: Optional[List[str]]
    business_model_codes: Optional[List[Literal["B2B", "B2C"]]]
