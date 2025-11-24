from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.sequence.step import ScheduleUnit, SequenceCampaignStep
from external.mautic.schema.person import MauticField

BASE_STEP = "leadsource"
BASE_STEP_ID = "lists"


class AnchorType(Enum):
    LEAD_SOURCE = "leadsource"
    TOP = "top"
    BOTTOM = "bottom"


class Type(Enum):
    SEND_EMAIL = "email.send"
    DECISION = "dwc.decision"
    CHANGE_LIST = "lead.changelist"
    VALID_EMAIL_CHECK = "email.validate.address"


class EventType(Enum):
    DECISION = "decision"
    ACTION = "action"
    CONDITION = "condition"


class DecisionPath(Enum):
    YES = "yes"
    NO = "no"


class EmailType(Enum):
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"


class Property(BaseModel):
    email: Optional[str]
    email_type: Optional[EmailType]
    addToLists: List[str] = []  # List of segment ids
    removeFromLists: List[str] = []  # List of segment ids


class TriggerMode(Enum):
    DATE = "date"
    INTERVAL = "interval"
    IMMEDIATE = "immediate"


class TriggerIntervalUnit(Enum):
    DAYS = "d"
    HOURS = "h"
    MINUTES = "i"
    MONTHS = "m"
    YEARS = "y"


SS_TRIGGER_INTERVAL_UNIT_MAPPING = {
    ScheduleUnit.DAYS: TriggerIntervalUnit.DAYS,
    ScheduleUnit.HOURS: TriggerIntervalUnit.HOURS,
    ScheduleUnit.MINUTES: TriggerIntervalUnit.MINUTES,
}


class MauticCampaignSegment(BaseModel):
    id: str
    name: Optional[str]


class MauticCampaignEvent(BaseModel):
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    type: Optional[Type]
    eventType: Optional[EventType]
    order: Optional[int]
    properties: Optional[Property]
    triggerInterval: Optional[int]
    triggerIntervalUnit: Optional[TriggerIntervalUnit]
    triggerMode: Optional[TriggerMode]
    decisionPath: Optional[DecisionPath]


class Anchor(BaseModel):
    source: Optional[AnchorType]
    target: Optional[AnchorType]


class Connection(BaseModel):
    anchors: Optional[Anchor]
    sourceId: Optional[str]
    targetId: Optional[str]


class CanvasSetting(BaseModel):
    connections: List[Connection] = []


class MauticCampaign(BaseModel):
    id: Optional[int]
    name: Optional[str]
    description: Optional[str]
    isPublished: Optional[bool]
    events: List[MauticCampaignEvent] = []
    lists: List[MauticCampaignSegment] = []
    canvasSettings: Optional[CanvasSetting]


class MauticSegmentResponse(BaseModel):
    list: MauticCampaignSegment


class MauticCampaignResponse(BaseModel):
    campaign: MauticCampaign


class MauticTriggerEventRequest(BaseModel):
    content: str
    lead: MauticField
    subject: str
    source: List


class MauticEditCampaignInput(SequenceCampaignStep):
    external_mautic_mail_template_id: int
    external_mautic_event_id: Optional[int]
