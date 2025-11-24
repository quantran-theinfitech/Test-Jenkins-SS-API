from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel

from app.api.v1.schemas.search_press_releases import SearchPressReleaseRequest
from app.api.v1.schemas.search_recruits import SearchRecruitRequest
from app.models.scenario import TypeCode


class ScenarioSettingRequest(BaseModel):
    name: str
    description: Optional[str]
    target_email: Optional[str]
    target_slack_connection_id: Optional[int]
    email_notification_flag: Optional[bool]
    slack_notification_flag: Optional[bool]

    """
        Vấn đề: Khi dùng Union type:
            + Pydantic sẽ match với type đầ u tiên được định nghĩa trong list,
            đồng thời lúc đó trong config của model thì extra_field="ignore"
            sẽ bỏ qua các field không được định nghĩa trong type đầu tiên.
            -> Vì vậy khi client gửi request có trigger_condition thuộc kiểu
            SearchPressReleaseRequest nó sẽ luôn bị bỏ qua.
        Giải pháp:
            + Thêm:
                class Config:
                    extra_field="forbid"
             vào 2 type SearchRecruitRequest và SearchPressReleaseRequest
        Giải thích:
            extra = 'forbid' in config means that additional attributes, that are not
            defined by given schema are not allowed. That makes pydantic not accepting
            the first type, but proceeding to the next ones.
    """
    trigger_conditions: Optional[Union[SearchRecruitRequest, SearchPressReleaseRequest]]
    type_code: Optional[TypeCode]


class ScenarioManagementItem(BaseModel):
    id: int
    name: Optional[str]
    type_code: Optional[str]
    description: Optional[str]
    target_email: Optional[str]
    email_notification_flag: Optional[bool]
    target_slack_connection_id: Optional[int]
    channel_name: Optional[str]
    slack_notification_flag: Optional[bool]
    created_by: Optional[str]
    today_count: Optional[int]
    yesterday_count: Optional[int]
    last_7_days_count: Optional[int]


class ScenarioManagementResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[ScenarioManagementItem]


class SearchScenarioResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    trigger_conditions: Optional[
        Union[SearchRecruitRequest, SearchPressReleaseRequest]
    ] = None


class ScenarioDetailResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    trigger_conditions: Optional[
        Union[SearchRecruitRequest, SearchPressReleaseRequest]
    ] = None
    description: Optional[str] = None
    target_email: Optional[str] = None
    target_slack_connection_id: Optional[int] = None
    email_notification_flag: Optional[bool] = None
    slack_notification_flag: Optional[bool] = None
    type_code: Optional[TypeCode] = None
    notification_updated_at: Optional[datetime] = None


class ScenarioNotification(BaseModel):
    id: Optional[int] = None
    target_email: Optional[str] = None
    channel_name: Optional[str] = None
    created_at: Optional[datetime] = None
    email_notify_at: Optional[datetime] = None
    slack_notify_at: Optional[datetime] = None
    count_item: Optional[int] = None


class ScenarioNotificationResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[ScenarioNotification]


class ScenarioNotificationItem(BaseModel):
    id: Optional[int] = None
    corporate_number: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    large_industry: Optional[str] = None
    president_name: Optional[str] = None
    media_code: Optional[str] = None
    large_category: Optional[str] = None
    medium_category: Optional[str] = None
    small_category: Optional[str] = None
    recruit_tels: Optional[List[str]] = None
    recruit_mails: Optional[List[str]] = None
    company_tel: Optional[str] = None
    contact_email: Optional[str] = None
    hp_url: Optional[str] = None
    contact_form_url: Optional[str] = None
    created_at: Optional[datetime] = None
    source_recruit_url: Optional[str] = None


class ListingScenarioNotificationItemsResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[ScenarioNotificationItem]


class UpdateScenarioRequest(BaseModel):
    email_notification_flag: Optional[bool]
    slack_notification_flag: Optional[bool]
    name: Optional[str]
    description: Optional[str]
    target_email: Optional[str]
    target_slack_connection_id: Optional[int]


class ScenarioMessage(BaseModel):
    id: int
    ingest_ids: List[str]
    target_email: Optional[str]
    target_slack: Optional[str]
    email_notification_flag: Optional[bool]
    slack_notification_flag: Optional[bool]
