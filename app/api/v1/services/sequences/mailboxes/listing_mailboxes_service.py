from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.mailboxes import MailboxBase
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mailboxes.get_detail_mailbox_service import (
    get_config_step_status_service,
)
from app.models.sequence.mail_alias import SequenceMailAlias
from app.models.sequence.mailbox import SequenceMailbox
from app.models.team import PlanCode
from app.models.team_credit import ServiceCode, TeamCredit


def listing_mailboxes_service(
    db: Session,
    current_user: UserBase,
    page: int,
    per_page: int,
):
    condition = [
        SequenceMailbox.team_id == current_user.team_id,
        SequenceMailbox.deleted_at.is_(None),
    ]
    query = (
        select(SequenceMailbox)
        .where(*condition)
        .order_by(SequenceMailbox.is_default.desc(), SequenceMailbox.id)
    )
    if per_page > 0:
        query = query.offset((page - 1) * per_page).limit(per_page)
    mailboxes = db.exec(query).all()
    ret = []
    for mailbox in mailboxes:
        query = select(SequenceMailAlias).where(
            SequenceMailAlias.sequence_mailbox_id == mailbox.id
        )
        query = query.order_by(
            SequenceMailAlias.is_default.desc(), SequenceMailAlias.id.desc()
        )
        mail_aliases = db.exec(query).all()
        count_alias = db.exec(
            query.with_only_columns(func.count(SequenceMailAlias.id)).order_by(None)
        ).first()
        config_status = get_config_step_status_service(mailbox.id, db, mailbox)
        ret.append(
            MailboxBase(
                **mailbox.dict(),
                count_alias_mailbox=(count_alias - 1) if count_alias > 0 else 0,
                config_step_status=config_status,
                mail_aliases=mail_aliases,
                is_current_user=True if mailbox.user_id == current_user.id else False,
            )
        )
    return ret


def count_listing_mailboxes_service(
    db: Session,
    current_user: UserBase,
):
    condition = [
        SequenceMailbox.team_id == current_user.team_id,
        SequenceMailbox.deleted_at.is_(None),
    ]
    query = select(func.count(SequenceMailbox.id)).where(*condition)
    count = db.exec(query).one()
    credits = db.exec(
        select(TeamCredit).where(
            TeamCredit.team_id == current_user.team_id,
            TeamCredit.start_at <= datetime.now(),
            TeamCredit.end_at >= datetime.now(),
            TeamCredit.is_active.is_(True),
        )
    ).all()
    if not any(c.service_code == ServiceCode.MAILBOX_CONNECT for c in credits):
        return count, 0
    if any(
        c.plan_code == PlanCode.UNLIMITED
        and c.service_code == ServiceCode.MAILBOX_CONNECT
        for c in credits
    ):
        return count, -1
    return count, sum(
        c.amount for c in credits if c.service_code == ServiceCode.MAILBOX_CONNECT
    )
