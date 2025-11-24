from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class CustomerContactStageCode(Enum):
    POTENTIAL = "POTENTIAL"
    LOST = "LOST"
    NEW = "NEW"


class ContactBase(BaseModel):
    id: Optional[int] = None
    team_id: Optional[int] = None
    corporate_number: Optional[List[str]] = []
    person_uuid: Optional[str] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    skills: Optional[str] = None
    company_name: Optional[str] = None
    status_code: Optional[CustomerContactStageCode] = "NEW"
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None
    note_url: Optional[str] = None
    fb_url: Optional[str] = None
    contact_times: Optional[int] = 0
    inbox_times: Optional[int] = 0
    potential_action_at: Optional[datetime]
    site_usage_at: Optional[datetime]
    change_history_at: Optional[datetime]
    lead_source_code: Optional[str] = None
    tags: Optional[List[str]]


class ListingContactsResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[ContactBase]


class SaveContactRequest(BaseModel):
    data: ContactBase


class ContactListFieldName(Enum):
    NAME = "name"
    BIO = "bio"
    EMAIL = "email"
    ADDRESS = "address"
    SKILLS = "skills"
    COMPANY_NAME = "company_name"
    STATUS_CODE = "status_code"
    LINKEDIN_URL = "linkedin_url"
    TWITTER_URL = "twitter_url"
    GITHUB_URL = "github_url"
    NOTE_URL = "note_url"
    FB_URL = "fb_url"
    CONTACT_TIMES = "contact_times"
    INBOX_TIMES = "inbox_times"
    POTENTIAL_ACTION_AT = "potential_action_at"
    SITE_USAGE_AT = "site_usage_at"
    CHANGE_HISTORY_AT = "change_history_at"
    LEAD_SOURCE_CODE = "lead_source_code"
