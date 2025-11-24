from datetime import datetime, timedelta

from jose import jwt
from sqlmodel import Session, select, update

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.config import settings
from app.models.team_invitation import TeamInvitation
from app.models.user import RoleCode, Source, User


def accept_invitation(db: Session, token: str):
    try:
        invitation = db.exec(
            select(TeamInvitation).where(TeamInvitation.token == token)
        ).first()

        if not invitation:
            error_message = "inviteMember.invitationExpired"
            raise BadRequestException(
                detail={"message": error_message, "is_register": False}
            )

        if (
            invitation.accepted_at
            or invitation.rejected_at
            or (
                invitation.created_at is None
                or (datetime.now() - invitation.created_at) > timedelta(hours=24)
            )
        ):
            user = db.exec(
                select(User).where(
                    User.email == invitation.email,
                    User.deleted_at.is_(None),
                    User.team_id.isnot(None),
                )
            ).first()
            if user:
                is_register = True
            else:
                is_register = False

            error_message = "inviteMember.invitationExpired"
            raise BadRequestException(
                detail={"message": error_message, "is_register": is_register}
            )

        inviter = db.exec(select(User).where(User.id == invitation.inviter_id)).first()
        if not inviter:
            raise NotFoundException(detail="inviteMember.inviterNotFound")

        existed_invitee = db.exec(
            select(User).where(
                User.email == invitation.email,
                User.deleted_at.is_(None),
                User.email_verified_at.isnot(None),
                User.team_id.isnot(None),
            )
        ).first()

        response = None
        if not existed_invitee:
            response = _create_new_member(db, invitation, inviter)
        else:
            response = _change_team(db, invitation, existed_invitee, inviter)
            invitation.accepted_at = datetime.now()
            db.add(invitation)
            db.flush()

        db.exec(
            update(TeamInvitation)
            .where(
                TeamInvitation.email == invitation.email,
                TeamInvitation.accepted_at.is_(None),
                TeamInvitation.rejected_at.is_(None),
                TeamInvitation.token != invitation.token,
            )
            .values(rejected_at=datetime.now())
        )
        # invitation.accepted_at = datetime.now()
        db.add(invitation)
        db.commit()
        return response

    except Exception as e:
        db.rollback()
        raise e


def _create_new_member(db: Session, invitation: TeamInvitation, inviter: User):
    not_finished_register_user = db.exec(
        select(User).where(
            User.email == invitation.email,
            User.deleted_at.is_(None),
            User.team_id.is_(None),
        )
    ).first()

    token = None

    if not_finished_register_user:
        iat = datetime.now()
        exp = iat + timedelta(hours=24)
        token = jwt.encode(
            {
                "email": invitation.email,
                "iat": iat,
                "exp": exp,
            },
            settings.VERIFY_KEY,
            algorithm=settings.ALGORITHM,
        )
        not_finished_register_user.created_at = datetime.now()
        db.add(not_finished_register_user)
    else:
        new_user = User(
            email=invitation.email,
            role_code=RoleCode.User,
            source=Source.DIRECTLY_REGISTER,
            team_member_role_code=invitation.role,
            company_name=inviter.company_name,
            email_verified_at=datetime.now(),
        )
        db.add(new_user)

        iat = datetime.now()
        exp = iat + timedelta(hours=24)
        token = jwt.encode(
            {
                "email": invitation.email,
                "iat": iat,
                "exp": exp,
            },
            settings.VERIFY_KEY,
            algorithm=settings.ALGORITHM,
        )
    return {
        "register_token": token,
        "team_id": invitation.team_id,
        "company_name": inviter.company_name,
    }


def _change_team(
    db: Session, invitation: TeamInvitation, existed_invitee: User, inviter: User
):

    new_user = User(
        role_code=existed_invitee.role_code,
        email=existed_invitee.email,
        password=existed_invitee.password,
        name=existed_invitee.name,
        gender_code=existed_invitee.gender_code,
        linkedin_profile_url=existed_invitee.linkedin_profile_url,
        email_verified_at=existed_invitee.email_verified_at,
        department_name=existed_invitee.department_name,
        tel=existed_invitee.tel,
        expect_meeting_flag=existed_invitee.expect_meeting_flag,
        position_code=existed_invitee.position_code,
        flag_first_login=existed_invitee.flag_first_login,
        initial_password=existed_invitee.initial_password,
        source=existed_invitee.source,
        show_tutorial_flag=existed_invitee.show_tutorial_flag,
        avatar_path=existed_invitee.avatar_path,
        password_updated_at=existed_invitee.password_updated_at,
    )

    new_user.team_id = invitation.team_id
    new_user.team_member_role_code = invitation.role
    new_user.company_name = inviter.company_name

    existed_invitee.deleted_at = datetime.now()
    db.add(existed_invitee)
    db.flush()

    db.add(new_user)
    db.flush()

    return None
