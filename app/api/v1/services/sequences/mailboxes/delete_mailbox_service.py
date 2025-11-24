from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, and_, select, update

from app.api.v1.schemas.users import UserBase
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory
from app.models.sequence.mailbox import SequenceMailbox
from app.models.team_credit import ServiceCode, TeamCredit


def delete_mailbox_service(
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
    mailbox.deleted_at = datetime.now()
    default_mailbox = None
    if mailbox.is_default:
        mailbox.is_default = False
        mailboxes = db.exec(
            select(SequenceMailbox)
            .where(
                SequenceMailbox.team_id == current_user.team_id,
                SequenceMailbox.deleted_at.is_(None),
            )
            .order_by(SequenceMailbox.id)
        ).all()
        if mailboxes:
            mailboxes[0].is_default = True
            db.add(mailboxes[0])
            default_mailbox = mailboxes[0]
    else:
        default_mailbox = db.exec(
            select(SequenceMailbox).where(
                SequenceMailbox.team_id == current_user.team_id,
                SequenceMailbox.deleted_at.is_(None),
                SequenceMailbox.is_default.is_(True),
            )
        ).first()
    db.exec(
        update(SequenceMailHistory)
        .where(
            and_(
                SequenceMailHistory.sequence_mailbox_id == mailbox_id,
                SequenceMailHistory.status.in_([MailHistoryStatus.SCHEDULED]),
                SequenceMailHistory.deleted_at.is_(None),
            )
        )
        .values(sequence_mailbox_id=default_mailbox.id if default_mailbox else None)
    )
    team_credit = db.exec(
        select(TeamCredit)
        .where(TeamCredit.team_id == current_user.team_id)
        .where(TeamCredit.service_code == ServiceCode.MAILBOX_CONNECT)
        .where(TeamCredit.deleted_at.is_(None))
        .where(TeamCredit.used_amount > 0)
    ).first()
    if team_credit:
        team_credit.used_amount -= 1
    db.commit()
