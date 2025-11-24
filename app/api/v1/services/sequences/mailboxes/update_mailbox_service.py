from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.mail_aliases import ListingMailAliases
from app.api.v1.schemas.sequence.mailboxes import MailboxBase, UpdateMailboxRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.mail_alias import SequenceMailAlias
from app.models.sequence.mailbox import SequenceMailbox
from external.google import GoogleService


def update_mailbox_service(
    mailbox_id: int,
    request: UpdateMailboxRequest,
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

    try:
        # Handle setting default mailbox logic if request.is_default is True
        if hasattr(request, "is_default") and request.is_default:
            # Find previous default mailbox (if any)
            previous_default = db.exec(
                select(SequenceMailbox).where(
                    SequenceMailbox.team_id == current_user.team_id,
                    SequenceMailbox.is_default.is_(True),
                    SequenceMailbox.deleted_at.is_(None),
                    SequenceMailbox.id != mailbox_id,  # Exclude current mailbox
                )
            ).first()

            # Unset previous default if it exists
            if previous_default:
                previous_default.is_default = False
                db.add(previous_default)

        # Update other fields from the request
        for key, value in request.dict(
            exclude_unset=True, exclude={"is_different_smtp_credentials"}
        ).items():
            setattr(mailbox, key, value)

        if (
            not request.is_different_smtp_credentials
            and request.is_different_smtp_credentials is not None
        ):
            mailbox.imap_email = request.email
            mailbox.imap_password = request.password

        mailbox.updated_at = datetime.now()
        mailbox.updated_by = current_user.id
        db.add(mailbox)
        db.commit()
        db.refresh(mailbox)
        return MailboxBase(**mailbox.dict())
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update mailbox: {str(e)}"
        )


def refresh_mail_alias_service(
    mailbox_id: int,
    db: Session,
):
    mail_aliases_resp = []
    duplicated_aliases = []
    mailbox = db.exec(
        select(SequenceMailbox).where(SequenceMailbox.id == mailbox_id)
    ).first()
    if not mailbox:
        raise HTTPException(status_code=404, detail="sequence.mailboxNotFound")
    if not mailbox.google_refresh_token:
        raise HTTPException(status_code=400, detail="sequence.missingRefereshToken")
    service = GoogleService()
    aliases = service.get_mail_aliases(mailbox.google_refresh_token)
    existed_aliases = db.exec(
        select(SequenceMailAlias).where(
            SequenceMailAlias.sequence_mailbox_id == mailbox.id
        )
    ).all()
    for existed_alias in existed_aliases:
        duplicated_alias = next(
            (
                mail_alias
                for mail_alias in aliases
                if mail_alias.get("sendAsEmail") == existed_alias.alias_email
            ),
            None,
        )
        if duplicated_alias:
            duplicated_aliases.append(duplicated_alias)
            existed_alias.alias_name = duplicated_alias.get("displayName", "")
            existed_alias.alias_signature = duplicated_alias.get("signature", "")
            existed_alias.is_default = duplicated_alias.get("isDefault", False)
            existed_alias.is_primary = duplicated_alias.get("isPrimary", False)
            existed_alias.updated_at = datetime.now()
            db.add(existed_alias)
            mail_aliases_resp.append(existed_alias)
        else:
            db.delete(existed_alias)
    for alias in aliases:
        if alias not in duplicated_aliases:
            mail_alias = SequenceMailAlias(
                sequence_mailbox_id=mailbox.id,
                alias_email=alias.get("sendAsEmail"),
                alias_name=alias.get("displayName", ""),
                alias_signature=alias.get("signature", ""),
                is_default=alias.get("isDefault", False),
                is_primary=alias.get("isPrimary", False),
            )
            db.add(mail_alias)
            mail_aliases_resp.append(mail_alias)
    db.commit()
    for alias in mail_aliases_resp:
        db.refresh(alias)
    return ListingMailAliases(list=mail_aliases_resp)


def listing_mail_alias_service(
    mailbox_id: int,
    db: Session,
):
    mail_aliases = db.exec(
        select(SequenceMailAlias).where(
            SequenceMailAlias.sequence_mailbox_id == mailbox_id
        )
    ).all()
    return ListingMailAliases(list=mail_aliases)
