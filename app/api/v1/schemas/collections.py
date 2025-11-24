from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.models.company_collection import StatusCode


class CreateCollectionMode(Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class TypeDownloadCompany(str, Enum):
    CREDIT = "CREDIT"
    DOWNLOADED = "DOWNLOADED"


class CompanyCollectionFieldName(Enum):
    COMPANY_NAME = "会社名"
    FORM_URL = "フォームURL"


class TypeCode(Enum):
    CSV = "CSV"
    SYS = "SYS"


class CSVCompanyCollectionFieldName(Enum):
    CORPORATE_NUMBER = "法人番号"
    NAME = "企業名"
    HP_URL = "ウェブサイトURL(@を除く)"
    INDUSTRY_CODE = "大業界"
    SUB_INDUSTRIES_CODE = "中業界"
    CLOSING_MONTH = "決算月"
    ADDRESS = "住所"
    BUSINESS_CONTENT = "事業内容"
    POSTAL_CODE = "郵便番号"
    ESTABLISH_AT = "設立年月日"
    LISTING_MARKET_CODE = "上場区分"
    PRESIDENT_NAME = "代表者名"
    PHONE = "代表電話番号"
    FAX = "FAX番号"
    CONTACT_EMAIL = "代表メールアドレス"
    RECRUIT_PHONE = "採用電話番号"
    RECRUIT_EMAIL = "採用メールアドレス"
    CONTACT_FORM_URL = "問い合わせフォーム"
    FACEBOOK_URL = "Facebook"
    TWITTER_URL = "Twitter"
    YOUTUBE_URL = "Youtube"
    EMPLOYEES_COUNT = "従業員数"
    CAPITAL = "資本金 (万円)"
    REVENUE = "売上（万円)"


class CSVPersonCollectionFieldName(Enum):
    ADDRESS = "住所"
    EMAIL = "メール"
    BIO = "自己紹介"
    FB_URL = "フェイスブックのURL"
    ROLE_GROUP_CODES = "役職グループ"
    ROLE_NAME = "役職"
    GITHUB_URL = "ギットハブのURL"
    CORPORATE_NUMBER = "法人番号"
    INTRO = "情報"
    COMPANY_NAME = "企業名"
    NAME = "氏名"
    LINKEDIN_URL = "リンクインのURL"
    TWITTER_URL = "ツイッターのURL"
    WANTEDLY_URL = "ワンテドリーのURL"


class CreateCollectionRequest(BaseModel):
    name: str
    group_id: Optional[int] = None
    tags: Optional[List[str]] = None
    mode: Optional[CreateCollectionMode]
    corporate_numbers: Optional[List[str]] = None
    description: Optional[str] = None
    search_condition: Optional[SearchCrossRequest] = None
    step: Optional[int] = None
    statusCode: Optional[StatusCode] = None
    main_person_id: Optional[int] = None


class UpdateCollectionRequest(BaseModel):
    name: Optional[str]
    group_id: Optional[int]
    description: Optional[str]
    status_code: Optional[StatusCode]


class AddCollectionItemsRequest(BaseModel):
    type_download: Optional[TypeDownloadCompany]
    collection_names: Optional[List[str]] = None
    corporate_numbers: Optional[List[str]] = None
    search_condition: Optional[SearchCrossRequest] = None


class AddCollectionItemsByCSVRequest(BaseModel):
    collection_id: Optional[int] = None
    collection_names: Optional[List[str]] = None


class CompanyCollection(BaseModel):
    id: Optional[int] = None
    team_id: Optional[int] = None
    name: Optional[str] = None
    group_id: Optional[int] = None
    description: Optional[str] = None
    status_code: Optional[StatusCode] = None
    mode_code: Optional[CreateCollectionMode] = None


class CompanyColecionTag(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class CollectionBase(BaseModel):
    id: int
    team_id: Optional[int] = None
    name: Optional[str] = None
    group_id: Optional[int] = None
    description: Optional[str] = None
    status_code: Optional[StatusCode] = None
    type_code: Optional[str] = None
    step: Optional[int] = None
    csv_path: Optional[str] = None
    search_condition: Optional[SearchCrossRequest] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class GetCollectionDetailResponse(CollectionBase):
    companies_count: Optional[int] = None
    tags: Optional[List[CompanyColecionTag]] = None


class GetDraftCollectionDetailResponse(CollectionBase):
    companies_count: Optional[int] = None
    tags: Optional[List[CompanyColecionTag]] = None
    corporate_numbers: Optional[List[str]] = None
    main_person_id: Optional[int] = None


class Collection(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    status_code: StatusCode
    companies_count: Optional[int] = 0
    tags: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    type_code: Optional[TypeCode] = None


class ListingCollectionsResponse(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    data: List[Collection]


class CheckCSVCollectionResponse(BaseModel):
    collection_id: Optional[int] = None


class AddCollectionItemByCSVResponse(BaseModel):
    collection_ids: Optional[List[int]] = None
