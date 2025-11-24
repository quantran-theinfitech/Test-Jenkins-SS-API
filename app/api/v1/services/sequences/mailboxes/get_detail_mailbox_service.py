import re
from typing import Optional

import dns
from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.api.base.exceptions import PaymentRequiredException
from app.api.v1.schemas.sequence.mailboxes import MailboxBase
from app.api.v1.schemas.users import UserBase
from app.models.sequence.mail_alias import SequenceMailAlias
from app.models.sequence.mailbox import MailboxType, SequenceMailbox
from app.models.team import PlanCode, Team
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit


def get_detail_mailbox_service(
    mailbox_id: int,
    db: Session,
    current_user: UserBase,
):
    condition = [
        SequenceMailbox.id == mailbox_id,
        SequenceMailbox.team_id == current_user.team_id,
        SequenceMailbox.deleted_at.is_(None),
    ]
    query = select(SequenceMailbox).where(*condition)
    mailbox = db.exec(query).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="sequence.mailboxNotFound")
    query = select(SequenceMailAlias).where(
        SequenceMailAlias.sequence_mailbox_id == mailbox.id
    )
    mail_aliases = db.exec(query.order_by(SequenceMailAlias.id.desc())).all()
    count_alias = db.exec(
        query.with_only_columns(func.count(SequenceMailAlias.id))
    ).first()
    return MailboxBase(
        **mailbox.dict(),
        count_alias_mailbox=(count_alias - 1) if count_alias > 0 else 0,
        config_step_status=get_config_step_status_service(mailbox.id, db, mailbox),
        mail_aliases=mail_aliases,
        is_current_user=True if current_user.id == mailbox.user_id else False,
    )


def get_mailbox_verify_status(
    mailbox_id: int,
    db: Session,
):
    mailbox = db.get(SequenceMailbox, mailbox_id)
    if not mailbox_id:
        raise HTTPException(status_code=404, detail="sequence.mailboxNotFound")

    match = re.search(r"@[\w.]+", mailbox.email)
    if not match:
        raise HTTPException(status_code=404, detail="sequence.mailboxDomainNotFound")
    domain = match.group()[1:]
    if domain == "gmail.com":
        return {
            "is_spf_verified": True,
            "is_dkim_verified": True,
        }
    is_spf_verified = False
    is_dkim_verified = False
    try:
        # Query for SPF records (type: TXT)
        answers = dns.resolver.resolve(domain, "TXT")
        for rdata in answers:
            # SPF records are typically stored in TXT records
            if rdata.to_text().startswith('"v=spf1'):
                is_spf_verified = True
                break

        if mailbox.mailbox_type == MailboxType.GOOGLE_API:
            dkim_record_name = f"google._domainkey.{domain}"
        if mailbox.mailbox_type == MailboxType.SMTP:
            dkim_record_name = f"smtp._domainkey.{domain}"

        answers = dns.resolver.resolve(dkim_record_name, "TXT")

        for rdata in answers:
            is_dkim_verified = True
            break

    except dns.resolver.NoAnswer:
        print("No SPF record found.")
    except dns.resolver.NXDOMAIN:
        print("Domain does not exist.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        return {
            "is_spf_verified": is_spf_verified,
            "is_dkim_verified": is_dkim_verified,
        }


def get_config_step_status_service(
    mailbox_id: int,
    db: Session,
    sequence_mailbox: Optional[SequenceMailbox] = None,
):
    if sequence_mailbox:
        mailbox = sequence_mailbox
    else:
        mailbox = db.exec(
            select(SequenceMailbox).where(
                SequenceMailbox.id == mailbox_id,
            )
        ).first()
        if not mailbox:
            raise HTTPException(status_code=404, detail="sequence.mailboxNotFound")
    is_linking_done = (mailbox.email is not None and mailbox.password is not None) or (
        mailbox.google_refresh_token is not None
        and mailbox.mailbox_type == MailboxType.GOOGLE_API
    )
    is_signature_done = mailbox.email_signature is not None
    is_sending_limit_done = (
        mailbox.emails_sent_per_day is not None
        and mailbox.emails_sent_per_hour is not None
    )
    is_opt_out_done = (
        mailbox.is_opt_out_message_after_signature
        if mailbox.is_opt_out_message_after_signature is not None
        else False
    ) and mailbox.opt_out_message_after_signature is not None
    resp = get_mailbox_verify_status(mailbox_id, db)
    if isinstance(resp, str):
        is_domain_verify_done = False
    else:
        is_domain_verify_done = resp.get("is_spf_verified", False) and resp.get(
            "is_dkim_verified", False
        )
    return {
        "is_linking_done": is_linking_done,
        "is_signature_done": is_signature_done,
        "is_sending_limit_done": is_sending_limit_done,
        "is_opt_out_done": is_opt_out_done,
        "is_domain_verify_done": is_domain_verify_done,
    }


def get_mailbox_limit_service(
    db: Session,
    current_user: UserBase,
):
    team = db.get(Team, current_user.team_id)
    if team.listing_plan_code == PlanCode.UNLIMITED:
        return True
    if not is_enough_credit(db, current_user.team_id, 1, ServiceCode.MAILBOX_CONNECT):
        raise PaymentRequiredException("sequence.notEnoughMailboxConnectQuota")
    return True
