from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.sequence.mail_aliases import MailAliasBase
from app.models.sequence.mailbox import MailboxType


class MailboxConfigStepStatusResponse(BaseModel):
    is_linking_done: Optional[bool] = False
    is_signature_done: Optional[bool] = False
    is_sending_limit_done: Optional[bool] = False
    is_opt_out_done: Optional[bool] = False
    is_domain_verify_done: Optional[bool] = False


class MailboxBase(BaseModel):
    id: int
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    mailbox_type: Optional[MailboxType] = None
    email: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    imap_email: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    emails_sent_per_day: Optional[int] = None
    emails_sent_per_hour: Optional[int] = None
    email_signature: Optional[str] = None
    opt_out_message_after_signature: Optional[str] = None
    is_opt_out_message_after_signature: Optional[bool] = None
    is_open_tracking: Optional[bool] = None
    is_click_tracking: Optional[bool] = None
    is_include_one_click_unsubscribe_headers: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    count_alias_mailbox: Optional[int] = None
    config_step_status: Optional[MailboxConfigStepStatusResponse] = None
    mail_aliases: Optional[List[MailAliasBase]] = None
    is_current_user: Optional[bool] = None
    is_default: Optional[bool] = None


class VerifyDomainMailboxResponse(BaseModel):
    is_spf_verified: bool
    is_dkim_verified: bool


class AddMailboxRequest(BaseModel):
    email: str
    password: str
    is_different_smtp_credentials: Optional[bool] = False
    host: Optional[str] = None
    port: Optional[int] = None
    imap_email: Optional[str] = None
    imap_password: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    emails_sent_per_day: Optional[int] = 50
    emails_sent_per_hour: Optional[int] = 6
    email_signature: Optional[str] = None
    opt_out_message_after_signature: Optional[str] = None
    is_opt_out_message_after_signature: Optional[bool] = False
    is_open_tracking: Optional[bool] = False
    is_click_tracking: Optional[bool] = False
    is_include_one_click_unsubscribe_headers: Optional[bool] = False


class MailBoxList(BaseModel):
    page: int
    per_page: int
    total: int
    limit: int
    data: List[MailboxBase]


class UpdateMailboxRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    is_different_smtp_credentials: Optional[bool] = None
    host: Optional[str] = None
    port: Optional[int] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    emails_sent_per_day: Optional[int] = None
    emails_sent_per_hour: Optional[int] = None
    email_signature: Optional[str] = None
    opt_out_message_after_signature: Optional[str] = None
    is_opt_out_message_after_signature: Optional[bool] = None
    is_open_tracking: Optional[bool] = None
    is_click_tracking: Optional[bool] = None
    is_include_one_click_unsubscribe_headers: Optional[bool] = None
    is_default: Optional[bool] = None


class SimpleMailSenderResponse(BaseModel):
    id: int
    address: Optional[str]


class ListSimpleMailSenderResponse(BaseModel):
    data: Optional[List[SimpleMailSenderResponse]]
