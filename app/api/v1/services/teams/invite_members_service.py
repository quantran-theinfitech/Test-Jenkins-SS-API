import urllib.parse
from datetime import datetime

from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from sqlmodel import Session, select, update

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.teams import InviteMembersRequest
from app.api.v1.schemas.users import UserBase
from app.config import settings
from app.models.team_invitation import TeamInvitation
from app.models.user import TeamMemberRoleCode, User
from utils.create_token import create_token


def invite_members(
    db: Session,
    current_user: UserBase,
    request: InviteMembersRequest,
    background_tasks: BackgroundTasks,
    mail_connection: ConnectionConfig,
):
    try:
        if current_user.team_member_role_code != TeamMemberRoleCode.MANAGER:
            raise BadRequestException(detail="inviteMember.notManager")

        invite_member_emails = list(set(request.email))

        joined_users = db.exec(
            select(User)
            .where(User.email.in_(invite_member_emails))
            .where(User.team_id == current_user.team_id)
            .where(User.deleted_at.is_(None))
        ).all()

        if len(joined_users) == len(invite_member_emails):
            raise BadRequestException(detail="inviteMember.allUsersAlreadyJoined")

        invite_member_emails = [
            email for email in invite_member_emails if email not in joined_users
        ]

        # reject old invitations
        db.exec(
            update(TeamInvitation)
            .where(TeamInvitation.team_id == current_user.team_id)
            .where(TeamInvitation.email.in_(invite_member_emails))
            .where(TeamInvitation.rejected_at.is_(None))
            .where(TeamInvitation.accepted_at.is_(None))
            .values(rejected_at=datetime.now())
        )

        # create new invitations
        invitations = []
        fm = FastMail(mail_connection)
        for email in invite_member_emails:
            token = create_token(settings.INVITATION_TOKEN_LENGTH)
            invitation = TeamInvitation(
                team_id=current_user.team_id,
                inviter_id=current_user.id,
                email=email,
                role=request.role,
                token=token,
            )
            invitations.append(invitation)

            url = f"{settings.FE_URL}/accept-invite?token={urllib.parse.quote(token)}"

            mail_content = {
                "email": email,
                "url": url,
                "inviter_name": current_user.name,
            }
            message = MessageSchema(
                subject=f"SalesSmartの{current_user.name}チームに招待されました。",
                recipients=[email],
                template_body=mail_content,
                subtype=MessageType.html,
            )
            background_tasks.add_task(
                fm.send_message, message, "member_invitation_email.html"
            )

        db.add_all(invitations)
        db.commit()

        return invitations

    except Exception as e:
        db.rollback()
        raise e
