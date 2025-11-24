from typing import List, Optional

from pydantic import BaseModel


class InboxGmailDetail(BaseModel):
    sender: Optional[str]
    subject: Optional[str]
    body: Optional[str]


class ListingGmails(BaseModel):
    gmails_list: List[InboxGmailDetail]


class GoogleBounceInfo(BaseModel):
    message_id: Optional[str] = None
    bounce_code: Optional[str] = None
    diagnostic_code: Optional[str] = None
