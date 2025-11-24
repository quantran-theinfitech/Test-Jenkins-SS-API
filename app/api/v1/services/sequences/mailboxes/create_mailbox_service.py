import re
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, or_, select

from app.api.base.exceptions import PaymentRequiredException
from app.api.v1.schemas.sequence.mailboxes import AddMailboxRequest, MailboxBase
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.api.v1.services.sequences.mailboxes.get_detail_mailbox_service import (
    get_config_step_status_service,
)
from app.models.sequence.mailbox import MailboxType, SequenceMailbox
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit


def validate_email(email: str) -> bool:
    # Định dạng email hợp lệ theo tiêu chuẩn phổ biến
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(regex, email):
        return True
    else:
        return False


def create_mailbox_service(
    db: Session, current_user: UserBase, request: AddMailboxRequest
):
    if not is_enough_credit(db, current_user.team_id, 1, ServiceCode.MAILBOX_CONNECT):
        raise PaymentRequiredException("sequence.notEnoughMailboxConnectQuota")
    if not validate_email(request.email) or (
        request.imap_email and not validate_email(request.imap_email)
    ):
        raise HTTPException(status_code=400, detail="sequence.invalidEmail")
    condition = [
        SequenceMailbox.email == request.email,
    ]
    if request.imap_email:
        condition.append(SequenceMailbox.imap_email == request.imap_email)
    query = (
        select(SequenceMailbox)
        .where (SequenceMailbox.team_id == current_user.team_id)
        .where(or_(*condition))
        .where(SequenceMailbox.deleted_at.is_(None))
    )
    exsisted_mailbox = db.exec(query).first()
    if exsisted_mailbox:
        raise HTTPException(status_code=400, detail="sequence.emailAlreadyExist")
    try:
        consume_credit(
            db,
            current_user.team_id,
            1,
            service_code=ServiceCode.MAILBOX_CONNECT,
        )
        mailbox = SequenceMailbox(**request.dict())
        if not request.is_different_smtp_credentials:
            mailbox.imap_email = request.email
            mailbox.imap_password = request.password
        mailbox.mailbox_type = MailboxType.SMTP
        mailbox.user_id = current_user.id
        mailbox.team_id = current_user.team_id
        mailbox.created_at = datetime.now()
        mailbox.created_by = current_user.id
        mailbox.updated_at = datetime.now()
        mailbox.updated_by = current_user.id
        mailbox.config_step_done = [1]
        existed_mailbox = db.exec(
            select(SequenceMailbox).where(
                SequenceMailbox.team_id == current_user.team_id,
                SequenceMailbox.deleted_at.is_(None),
            )
        ).first()
        if existed_mailbox:
            mailbox.is_default = False
        else:
            mailbox.is_default = True
        db.add(mailbox)
        db.commit()
        db.refresh(mailbox)
        return MailboxBase(
            **mailbox.dict(),
            count_alias_mailbox=0,
            config_step_status=get_config_step_status_service(mailbox.id, db, mailbox)
        )
    except Exception:
        db.rollback()
        raise