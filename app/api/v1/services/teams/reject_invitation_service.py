from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.api.base.exceptions import BadRequestException
from app.models.team_invitation import TeamInvitation
from app.models.user import User


def reject_invitation(db: Session, token: str):
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

    invitation.rejected_at = datetime.now()
    db.add(invitation)
    db.commit()
