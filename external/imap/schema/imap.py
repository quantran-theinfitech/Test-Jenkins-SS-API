from typing import Optional

from pydantic import BaseModel


class IMAPBounceInfo(BaseModel):
    message_id: Optional[str] = None
    references: Optional[str] = None
    subject: Optional[str] = None
    original_recipient: Optional[str] = None
    bounce_code: Optional[str] = None
    diagnostic_code: Optional[str] = None
