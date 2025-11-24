from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MailAliasBase(BaseModel):
    id: int
    sequence_mailbox_id: Optional[int]
    alias_email: Optional[str]
    alias_name: Optional[str]
    alias_signature: Optional[str]
    is_default: Optional[bool]
    is_primary: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ListingMailAliases(BaseModel):
    list: List[MailAliasBase] = []
