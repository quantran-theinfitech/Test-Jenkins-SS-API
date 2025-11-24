from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.models.team_invitation import TeamInvitation
from app.models.user import User


def validate_invitation_token(db: Session, token: str):
    invitation = db.exec(
        select(TeamInvitation).where(TeamInvitation.token == token)
    ).first()

    if not invitation:
        error_message = "inviteMember.invitationExpired"
        raise BadRequestException(detail={"message": error_message, "is_register": False})
    
    if invitation.accepted_at or invitation.rejected_at or (invitation.created_at is None or (datetime.now() - invitation.created_at) > timedelta(hours=24)):
        user = db.exec(select(User).where(User.email == invitation.email, User.deleted_at.is_(None), User.team_id.isnot(None))).first()
        if user:
            is_register = True
        else:
            is_register = False
        
        error_message = "inviteMember.invitationExpired"
        raise BadRequestException(detail={"message": error_message, "is_register": is_register})

    inviter = db.exec(select(User).where(User.id == invitation.inviter_id)).first()

    invitee = db.exec(
        select(User).where(
            User.email == invitation.email,
            User.deleted_at.is_(None),
            User.email_verified_at.isnot(None),
            User.team_id.isnot(None),
        )
    ).first()

    if not inviter:
        raise NotFoundException(detail="inviteMember.inviterNotFound")

    return {
        "inviter_name": inviter.name,
        "inviter_email": inviter.email,
        "role": invitation.role,
        "is_new_user": invitee is None,
        "company_name": inviter.company_name,
    }
