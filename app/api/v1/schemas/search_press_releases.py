from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel


class PressReleaseType(BaseModel):
    operator: Optional[Literal["AND", "OR"]]

    # Ex: [イベント, 人物, 商品サビース, ...]
    press_release_types: Optional[List[str]]


class Industries(BaseModel):
    large_industries: Optional[List[str]]
    sub_industries: Optional[List[str]]


class Location(BaseModel):
    prefectures: Optional[List[int]]
    cities: Optional[List[int]]


class Keyword(BaseModel):
    and_keywords: Optional[List[str]]
    or_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]
    is_exact: Optional[bool]


class PostingPeriod(str, Enum):
    ONE_MONTH = "ONE_MONTH"
    ONE_TO_THREE_MONTH = "ONE_TO_THREE_MONTH"
    THREE_TO_SIX_MONTH = "THREE_TO_SIX_MONTH"
    SIX_TO_ONE_YEAR = "SIX_TO_ONE_YEAR"
    ONE_YEAR_OR_MORE = "ONE_YEAR_OR_MORE"


class SearchPressReleaseRequest(BaseModel):
    keyword: Optional[Keyword] = None
    media: Optional[List[str]]
    posting_period: Optional[List[PostingPeriod]] = None
    business_categories: Optional[List[int]] = None
    type_codes: Optional[List[str]] = None

    class Config:
        extra = "allow"


class EsPressReleaseBase(BaseModel):
    media_code: Optional[str]
    source_article_url: Optional[str]
    corporate_number: Optional[str]
    company_name: Optional[str]

    type_code: Optional[str]
    title: Optional[str]
    sub_title: Optional[str]
    content: Optional[str]
    body_urls: Optional[List[str]]
    business_category_texts: Optional[List[str]]
    business_category_urls: Optional[List[str]]
    prtimes_location_info_texts: Optional[List[str]]
    prtimes_location_info_urls: Optional[List[str]]
    keyword_texts: Optional[List[str]]
    keyword_urls: Optional[List[str]]

    posted_at_raw: Optional[str]
    posted_at: Optional[datetime]
    article_company_id: Optional[str]

    # company
    recruit_tags: Optional[List[str]]
    skill_codes: Optional[List[str]]
    recruit_qualifications: Optional[List[str]]
    tech_languages: Optional[List[str]]
    tech_frameworks: Optional[List[str]]
    tech_clouds: Optional[List[str]]
    tech_databases: Optional[List[str]]
    communication_tools: Optional[List[str]]
    management_tools: Optional[List[str]]
    internal_tools: Optional[List[str]]
    crm_tools: Optional[List[str]]
    kana_name: Optional[str]
    english_name: Optional[str]
    establish_at: Optional[datetime]
    nta_city_id: Optional[int]
    nta_prefecture_id: Optional[int]
    hp_url: Optional[str]
    domain: Optional[str]
    industry_code: Optional[str]
    sub_industries_code: Optional[List[str]]
    business_content: Optional[str]
    listing_market_code: Optional[str]
    twitter_url: Optional[str]
    facebook_url: Optional[str]
    contact_form_url: Optional[str]
    revenue: Optional[str]
    phone: Optional[str]
    recruit_phone: Optional[str]
    contact_email: Optional[str]
    recruit_email: Optional[str]

    capital: Optional[str]
    fax: Optional[str]
    closing_month: Optional[int]
    employees_count: Optional[int]
    average_age: Optional[str]
    press_release_media_codes: Optional[List[str]]
    recruit_media_codes: Optional[List[str]]
    business_model_codes: Optional[List[str]]


class PressReleaseResponse(EsPressReleaseBase):
    id: Optional[str]
    contact_email: Optional[str]
    hp_url: Optional[str]
    contact_form_url: Optional[str]
    company_downloaded_flag: Optional[bool] = None


class SearchPressReleaseResponse(BaseModel):
    page: int
    per_page: int
    total: int
    unlimited_total: int
    data: List[PressReleaseResponse]
