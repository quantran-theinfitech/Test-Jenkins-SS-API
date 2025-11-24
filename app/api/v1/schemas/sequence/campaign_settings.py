from typing import List, Optional

from pydantic import BaseModel

from app.models.sequence.contact import SequencePersonStage

from .schedules import ScheduleBase


class SequenceCampaignSettingBase(BaseModel):
    id: int
    sequence_campaign_id: int
    sequence_campaign_name: str
    sequence_campaign_owner: str
    sequence_schedule: ScheduleBase = None
    days_until_unresponsive: Optional[int] = None
    stage_list_as_not_sent: Optional[List[SequencePersonStage]] = []
    is_finished_when_replied: Optional[bool] = None
    is_finished_when_unsubscribed: Optional[bool] = None
    is_status_change_when_bounced: Optional[bool] = None
    cc_list: Optional[List] = []
    bcc_list: Optional[List] = []


class SequenceCampaignSettingResponse(SequenceCampaignSettingBase):
    is_owner_current_user: Optional[bool] = None
    sequence_schedule_list: Optional[List[ScheduleBase]] = []


class UpdateSequenceCampaignSettingRequest(BaseModel):
    sequence_schedule_id: Optional[int] = None
    days_until_unresponsive: Optional[int] = None
    stage_list_as_not_sent: Optional[List] = None
    cc_list: Optional[List] = None
    bcc_list: Optional[List] = None


class UpdateCampaignSettingRequest(BaseModel):
    sequence_name: Optional[str] = None
    sequence_schedule_id: Optional[int] = None
    days_until_unresponsive: Optional[int] = None
    stage_list_as_not_sent: Optional[List[SequencePersonStage]] = []
    is_finished_when_replied: Optional[bool] = None
    is_finished_when_unsubscribed: Optional[bool] = None
    is_status_change_when_bounced: Optional[bool] = None
    cc_list: Optional[List[str]] = []
    bcc_list: Optional[List[str]] = []
