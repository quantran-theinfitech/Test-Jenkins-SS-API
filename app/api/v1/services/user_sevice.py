# flake8: noqa
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytz
from fastapi import Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jose import jwt
from jose.exceptions import JWTError
from pydantic import EmailStr, ValidationError
from sqlalchemy import and_
from sqlmodel import Session, exists, func, select, update

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.api.v1.schemas.users import (
    ConfirmPolicyResponse,
    CreateUserRequest,
    CreateUserResponse,
    RefreshToken,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordResponse,
    Token,
    TokenData,
    TokenPayload,
    UpdateEmailRequest,
    UpdatePasswordRequest,
    UpdatePublicInformationRequest,
    UserBase,
    UserLoginRequest,
)
from app.api.v1.services import media as media_service
from app.api.v1.services.auth_service import AuthService
from app.config import settings
from app.models.group import Group
from app.models.plan import PlanServiceCode
from app.models.subcription import Subcription
from app.models.team import PlanCode, Team
from app.models.team_credit import ReasonCode, TeamCredit
from app.models.team_invitation import TeamInvitation
from app.models.user import RoleCode, Source, TeamMemberRoleCode, User

email_verification_failed = """
    <html>
        <head>
            <title>メール確認</title>
        </head>
        <body>
            <h2>資格情報を検証できませんでした</h2>
        </body>
    </html>
"""


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, data: RegisterRequest) -> RegisterResponse:
        auth_service = AuthService(self.db)

        token = data.token
        item = data.content

        try:
            payload = jwt.decode(
                token, settings.VERIFY_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenData(**payload)

            if token_data.email != item.email:
                raise BadRequestException(detail="auth.tokenInvalid")
        except (JWTError, ValidationError):
            raise BadRequestException(detail="auth.tokenInvalid")

        user = self.db.exec(
            select(User).where(
                and_(
                    User.email == item.email,
                    User.email_verified_at.isnot(None),
                    User.deleted_at.is_(None),
                )
            )
        ).first()

        if user is None:
            raise NotFoundException(detail="auth.userNotFound")

        user_created_at_utc = (
            user.created_at.replace(tzinfo=timezone.utc).replace(microsecond=0)
            if user.created_at.tzinfo is None
            else user.created_at.astimezone(timezone.utc).replace(microsecond=0)
        )

        if token_data.exp < datetime.now(timezone.utc):
            error_message = "auth.tokenExpired"
            raise BadRequestException(detail=error_message)

        if user_created_at_utc != token_data.iat:
            error_message = "auth.tokenExpired"
            raise BadRequestException(detail=error_message)

        team = None

        if data.invitation_token:
            invitation = self.db.exec(
                select(TeamInvitation).where(
                    TeamInvitation.token == data.invitation_token,
                    TeamInvitation.accepted_at.is_(None),
                    TeamInvitation.rejected_at.is_(None),
                    TeamInvitation.email == item.email,
                )
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
                user = self.db.exec(
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

            team = self.db.exec(
                select(Team).where(Team.id == invitation.team_id)
            ).first()
            if not team:
                raise NotFoundException(detail="auth.invitationTokenInvalid")

            user.team_id = team.id
            user.team_member_role_code = invitation.role
            self.db.exec(
                update(TeamInvitation)
                .where(TeamInvitation.token == data.invitation_token)
                .values(accepted_at=datetime.now())
            )

        else:
            new_team = Team(listing_plan_code=PlanCode.FRE, form_plan_code=PlanCode.FRE)
            self.db.add(new_team)
            self.db.flush()
            self.db.refresh(new_team)
            now = datetime.now(pytz.timezone("Asia/Tokyo"))
            start_of_next_month = (now.replace(day=1) + timedelta(days=32)).replace(
                day=1
            )
            new_listing_subscription = Subcription(
                team_id=new_team.id,
                plan_code=new_team.listing_plan_code,
                service_code=PlanServiceCode.LISTING,
                expire_at=(
                    start_of_next_month
                    if new_team.listing_plan_code != PlanCode.FRE
                    else None
                ),
                start_at=now,
            )
            new_form_subscription = Subcription(
                team_id=new_team.id,
                plan_code=new_team.form_plan_code,
                service_code=PlanServiceCode.FORM,
                expire_at=(
                    start_of_next_month
                    if new_team.form_plan_code != PlanCode.FRE
                    else None
                ),
                start_at=now,
            )
            self.db.add(new_listing_subscription)
            self.db.add(new_form_subscription)

            start_of_next_month = (now.replace(day=1) + timedelta(days=32)).replace(
                day=1
            )

            new_company_credit = TeamCredit(
                team_id=new_team.id,
                service_code=PlanServiceCode.CPN,
                plan_code=PlanCode.FRE,
                reason_code=ReasonCode.MONTHLY,
                amount=500,
                used_amount=0,
                start_at=now,
                end_at=start_of_next_month,
                is_active=True,
            )

            new_person_credit = TeamCredit(
                team_id=new_team.id,
                service_code=PlanServiceCode.PERSON,
                plan_code=PlanCode.FRE,
                reason_code=ReasonCode.MONTHLY,
                amount=20,
                used_amount=0,
                start_at=now,
                end_at=start_of_next_month,
                is_active=True,
            )

            self.db.add(new_company_credit)
            self.db.add(new_person_credit)

            new_group = Group(
                team_id=new_team.id,
                name="デフォルト",
                description="自動生成のグループ",
                default_flag=1,
            )
            self.db.add(new_group)
            user.team_id = new_team.id
            user.team_member_role_code = TeamMemberRoleCode.MANAGER

        user.company_name = item.company_name
        user.position_code = item.position_code
        user.department_name = item.department_name
        user.name = item.name
        user.email = item.email
        user.tel = item.tel
        user.password = auth_service.get_password_hash(item.password)
        user.expect_meeting_flag = item.expect_meeting_flag
        user.gender_code = item.gender_code
        user.linkedin_profile_url = item.linkedin_profile_url
        user.created_at = datetime.now(timezone.utc)
        user.team_member_role_code = TeamMemberRoleCode.MANAGER

        self.db.commit()

        return RegisterResponse(
            id=user.id,
            email=user.email,
            team_id=user.team_id,
            name=user.name,
            gender_code=user.gender_code,
            role_code=user.role_code,
        )

    async def send_verification_email(
        self, item: CreateUserRequest, mail_connection: ConnectionConfig
    ) -> CreateUserResponse:
        user = self.db.exec(
            select(User).where(User.email == item.email, User.deleted_at.is_(None))
        ).first()

        if (
            user is not None
            and user.email_verified_at is not None
            and user.password is not None
        ):
            raise ConflictException(detail="auth.userAlreadyExist")

        if user is not None:
            if datetime.now(timezone.utc) - user.created_at.replace(
                tzinfo=timezone.utc
            ) < timedelta(minutes=1):
                raise ConflictException(detail="auth.userSignUpTooFast")

            user.created_at = datetime.now(timezone.utc)
            self.db.commit()

            iat = user.created_at
            exp = iat + timedelta(hours=24)
        else:
            new_user = User(
                email=item.email,
                role_code=RoleCode.User,
                created_at=datetime.now(timezone.utc),
                source=Source.DIRECTLY_REGISTER,
            )

            self.db.add(new_user)
            self.db.commit()

            iat = new_user.created_at
            exp = iat + timedelta(hours=24)

        try:
            token = jwt.encode(
                {
                    "email": item.email,
                    "iat": iat,
                    "exp": exp,
                },
                settings.VERIFY_KEY,
                algorithm=settings.ALGORITHM,
            )

            url = f"{settings.FE_URL}/signup?step=3&token={urllib.parse.quote(token)}"
            template_data = {
                "url": url,
                "email": item.email,
            }
            message = MessageSchema(
                subject="【SalesSmart】のメンバーとして登録しました",
                recipients=[EmailStr(item.email)],
                template_body=template_data,
                subtype=MessageType.html,
            )
            fm = FastMail(mail_connection)

            await fm.send_message(message, template_name="register.html")
        except Exception as e:
            self.db.rollback()
            raise e

        return CreateUserResponse(expired_at=exp.isoformat())

    async def send_verification_email_for_forgot_password(
        self, item: CreateUserRequest, mail_connection: ConnectionConfig
    ) -> CreateUserResponse:
        user = self.db.exec(
            select(User).where(User.email == item.email, User.deleted_at.is_(None))
        ).first()

        if user is None:
            raise ConflictException(detail="auth.userNotFoundForgotPassword")

        if (
            user is not None
            and user.email_verified_at is not None
            and user.password is not None
        ):
            if (
                user.reset_password_at is not None
                and (datetime.now(timezone.utc) - user.reset_password_at.replace(tzinfo=timezone.utc)) < timedelta(minutes=1)
            ):
                raise ConflictException(detail="auth.userForgotPasswordTooFast")

            user.reset_password_at = datetime.now(timezone.utc)
            self.db.commit()

            iat = user.reset_password_at
            exp = iat + timedelta(hours=24)
        else:
            raise ConflictException(detail="auth.userNotFoundForgotPassword")

        try:
            token = jwt.encode(
                {
                    "email": item.email,
                    "iat": iat,
                    "exp": exp,
                },
                settings.VERIFY_KEY,
                algorithm=settings.ALGORITHM,
            )

            token_parse = urllib.parse.quote(token)

            url = f"{settings.FE_URL}/reset-password?token={token_parse}"
            template_data = {
                "user_name": user.name,
                "url": url,
                "email": item.email,
            }
            message = MessageSchema(
                subject="【SalesSmart】からのパスワードを再設定するためのお知らせです。",
                recipients=[EmailStr(item.email)],
                template_body=template_data,
                subtype=MessageType.html,
            )
            fm = FastMail(mail_connection)

            await fm.send_message(message, template_name="forgot_password.html")
        except Exception as e:
            self.db.rollback()
            raise e

        return CreateUserResponse(expired_at=exp.isoformat())

    def login_for_access_token(self, form_data: UserLoginRequest = Depends()) -> Token:
        auth_service = AuthService(self.db)
        first_login_user = auth_service.authenticate_user_with_init_password(
            form_data.email, form_data.password
        )
        login_with_init_pw = False
        user = None
        if first_login_user:
            if first_login_user.deleted_at:
                raise UnauthorizedException(detail="auth.userDeleted")
            user = first_login_user
            login_with_init_pw = True
        else:
            user = auth_service.authenticate_user(form_data.email, form_data.password)
            if not user:
                raise UnauthorizedException(detail="auth.incorrectEmailOrpassword")
            if user.deleted_at:
                raise UnauthorizedException(detail="auth.userDeleted")
            if not user.email_verified_at:
                raise ForbiddenException(detail="auth.haveNotVerifyEmail")

        user_base = UserBase(team_id=user.team_id, id=user.id, email=user.email)
        user_listing_plan = self.get_user_plan(user_base, PlanServiceCode.LISTING)
        user_form_plan = self.get_user_plan(user_base, PlanServiceCode.FORM)

        access_token, expire_at = auth_service.create_access_token(
            user.email,
            user_listing_plan,
            user_form_plan,
            login_with_init_pw,
            user.password_updated_at,
        )

        refresh_token, refresh_expire_at = auth_service.create_refresh_token(user.email)

        return Token(
            token_type="bearer",
            access_token=access_token,
            expire_at=expire_at,
            refresh_token=refresh_token,
            refresh_expire_at=refresh_expire_at,
            flag_first_login=user.flag_first_login,
            show_tutorial_flag=user.show_tutorial_flag,
            login_with_init_pw=login_with_init_pw,
        )

    def confirm_policy(self, current_user: UserBase) -> ConfirmPolicyResponse:
        user = self.db.exec(
            select(User).where(
                User.email == current_user.email, User.deleted_at.is_(None)
            )
        ).first()

        if not user:
            raise NotFoundException(detail="auth.userNotFound")

        if user.flag_first_login is False:
            raise ForbiddenException(detail="auth.haveConfirmedPolicyMessage")

        user.flag_first_login = False
        self.db.commit()
        self.db.refresh(user)

        return ConfirmPolicyResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            gender_code=user.gender_code,
            role_code=user.role_code,
            team_id=user.team_id,
            flag_first_login=user.flag_first_login,
        )

    def get_user_by_email(self, email: str) -> Optional[UserBase]:
        user = self.db.exec(
            select(User).where(User.email == email).order_by(User.updated_at.desc())
        ).first()
        if not user:
            return None

        return UserBase(
            id=user.id,
            email=user.email,
            name=user.name,
            team_member_role_code=user.team_member_role_code,
            gender_code=user.gender_code,
            role_code=user.role_code,
            team_id=user.team_id,
            flag_first_login=user.flag_first_login,
            avatar_path=user.avatar_path,
            deleted_at=user.deleted_at,
            password_updated_at=user.password_updated_at,
        )

    def refresh_token(
        self, input_token_refresh: RefreshToken, auth_service: AuthService
    ) -> Token:
        """
        OAuth2 compatible token, get an access token
        for future requests using refresh token
        """
        try:
            payload = jwt.decode(
                input_token_refresh.refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError):
            raise ForbiddenException(detail="auth.couldNotValidateCredentials")
        if not token_data.refresh:
            raise ForbiddenException(detail="auth.couldNotValidateCredentials")
        user = self.db.exec(
            select(User).where(User.email == token_data.sub, User.deleted_at.is_(None))
        ).first()

        if user is None:
            raise NotFoundException(detail="auth.userNotFound")

        user_base = UserBase(team_id=user.team_id, id=user.id, email=user.email)
        user_listing_plan = self.get_user_plan(user_base, PlanServiceCode.LISTING)
        user_form_plan = self.get_user_plan(user_base, PlanServiceCode.FORM)
        access_token, expire_at = auth_service.create_access_token(
            subject=user.email,
            listing_plan_code=user_listing_plan,
            form_plan_code=user_form_plan,
            password_updated_at=user.password_updated_at,
        )
        refresh_token, refresh_expire_at = auth_service.create_refresh_token(user.email)
        return Token(
            token_type="bearer",
            access_token=access_token,
            expire_at=expire_at,
            refresh_token=refresh_token,
            refresh_expire_at=refresh_expire_at,
            flag_first_login=user.flag_first_login,
            show_tutorial_flag=user.show_tutorial_flag,
        )

    def change_password(self, current_user: UserBase, password: str):
        auth_service = AuthService(self.db)
        password = auth_service.get_password_hash(password)
        user = self.db.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise NotFoundException(detail="auth.userNotFound")
        user.password = password
        self.db.add(user)
        self.db.commit()

    def verify_email(self, current_user: UserBase):
        user = self.db.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise NotFoundException(detail="auth.userNotFound")
        user.email_verified_at = datetime.now(timezone.utc)
        self.db.add(user)
        self.db.commit()

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(
                token, settings.VERIFY_KEY, algorithms=[settings.ALGORITHM]
            )
            data = TokenData(**payload)
        except (JWTError, ValidationError):
            error_message = "auth.tokenInvalid"
            raise BadRequestException(detail={"message": error_message, "email": ""})
        user = self.db.exec(
            select(User).where(User.email == data.email, User.deleted_at.is_(None))
        ).first()
        if not user:
            error_message = "auth.tokenInvalid"
            raise BadRequestException(
                detail={"message": error_message, "email": data.email}
            )

        user_created_at_utc = (
            user.created_at.replace(tzinfo=timezone.utc).replace(microsecond=0)
            if user.created_at.tzinfo is None
            else user.created_at.astimezone(timezone.utc).replace(microsecond=0)
        )

        if data.exp < datetime.now(timezone.utc):
            error_message = "auth.tokenExpired"
            raise BadRequestException(
                detail={"message": error_message, "email": data.email}
            )

        if user_created_at_utc != data.iat:
            error_message = "auth.tokenExpired"
            raise BadRequestException(
                detail={"message": error_message, "email": data.email}
            )

        user.email_verified_at = datetime.now(timezone.utc)

        self.db.add(user)
        self.db.commit()
        return data.email

    def verify_token_for_reset_password(self, token: str):
        try:
            payload = jwt.decode(
                token, settings.VERIFY_KEY, algorithms=[settings.ALGORITHM]
            )
            data = TokenData(**payload)
        except (JWTError, ValidationError):
            error_message = "auth.tokenInvalid"
            raise BadRequestException(detail={"message": error_message, "email": ""})
        user = self.db.exec(
            select(User).where(
                User.email == data.email,
                User.deleted_at.is_(None),
                User.email_verified_at.isnot(None),
            )
        ).first()

        if not user:
            error_message = "auth.tokenInvalid"
            raise BadRequestException(
                detail={"message": error_message, "email": data.email}
            )

        user_created_at_utc = (
            user.reset_password_at.replace(tzinfo=timezone.utc).replace(microsecond=0)
            if user.reset_password_at.tzinfo is None
            else user.reset_password_at.astimezone(timezone.utc).replace(microsecond=0)
        )

        if data.exp < datetime.now(timezone.utc):
            error_message = "auth.tokenExpired"
            raise BadRequestException(
                detail={"message": error_message, "email": data.email}
            )

        if user_created_at_utc != data.iat:
            error_message = "auth.tokenExpired"
            raise BadRequestException(
                detail={"message": error_message, "email": data.email}
            )

        return data.email

    def reset_password(self, token: str, password: str):
        try:
            email = self.verify_token_for_reset_password(token)
            user = self.db.exec(
                select(User).where(
                    User.email == email,
                    User.deleted_at.is_(None),
                    User.email_verified_at.isnot(None),
                )
            ).first()
            if not user:
                raise NotFoundException(detail="auth.userNotFound")

            auth_service = AuthService(self.db)
            user.password = auth_service.get_password_hash(password)
            user.reset_password_at = datetime.now()

            self.db.add(user)
            self.db.commit()
            return ResetPasswordResponse(
                detail="auth.resetPasswordSuccess"
            )
        except HTTPException as e:
            raise e

    def get_user_plan(
        self, current_user: UserBase, service_code: PlanServiceCode
    ) -> PlanCode:
        team = self.db.exec(
            select(Team.id, Team.listing_plan_code, Team.form_plan_code).where(
                current_user.team_id == Team.id
            )
        ).first()
        if team:
            if service_code == PlanServiceCode.LISTING:
                return team.listing_plan_code
            else:
                return team.form_plan_code
        else:
            raise NotFoundException(detail="team.teamNotFound")

    def get_active_platform(self, current_user: UserBase):
        team = self.db.exec(select(Team).where(current_user.team_id == Team.id)).first()
        if team:
            return team.active_platform
        else:
            raise NotFoundException(detail="team.teamNotFound")

    def get_integrated_platform(self, current_user: UserBase):
        team = self.db.exec(select(Team).where(current_user.team_id == Team.id)).first()
        if team:
            if team.active_platform:
                return team.integrated_platform
            else:
                return None
        else:
            raise NotFoundException(detail="team.teamNotFound")

    def hide_tutorial(self, current_user: UserBase):
        user = self.db.exec(
            select(User).where(
                User.email == current_user.email, User.deleted_at.is_(None)
            )
        ).first()

        if not user:
            raise NotFoundException(detail="auth.userNotFound")

        if not user.show_tutorial_flag:
            raise ForbiddenException(detail="auth.haveHideTutorialMessage")

        user.show_tutorial_flag = False
        self.db.commit()
        self.db.refresh(user)

        return True

    def update_public_information(
        self, current_user: UserBase, request: UpdatePublicInformationRequest
    ):
        user = self.db.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise NotFoundException(detail="auth.userNotFound")
        if request.name:
            user.name = request.name
        if request.avatar_path:
            stored_avatar_path = media_service.move_file_from_tmp_to_perm(
                request.avatar_path
            )
            user.avatar_path = stored_avatar_path

        self.db.add(user)
        self.db.commit()
        self.db.flush()
        return user

    def update_password(self, current_user: UserBase, request: UpdatePasswordRequest):
        if request.new_password != request.new_password_confirm:
            raise BadRequestException(detail="auth.confirmPasswordNotMatch")
        if request.new_password == request.old_password:
            return
        auth_service = AuthService(self.db)
        user = auth_service.authenticate_user(current_user.email, request.old_password)
        if not user:
            raise ForbiddenException(detail="auth.incorrectPassword")

        user.password = auth_service.get_password_hash(request.new_password)
        user.updated_at = datetime.now()
        if request.force_logout:
            user.password_updated_at = datetime.now()
        self.db.add(user)
        self.db.commit()

    def update_email(self, current_user: UserBase, request: UpdateEmailRequest):
        auth_service = AuthService(self.db)
        user = auth_service.authenticate_user(current_user.email, request.password)
        if not user:
            raise ForbiddenException(detail="auth.incorrectPassword")
        if user.email == request.new_email:
            raise BadRequestException(detail="auth.emailAlreadyUsed")
        existing_user = self.db.exec(
            select(User).where(
                User.email == request.new_email, User.deleted_at.is_(None)
            )
        ).first()
        if existing_user is not None:
            raise ConflictException(detail="auth.userAlreadyExist")
        user.email = request.new_email
        user.updated_at = datetime.now()
        self.db.add(user)
        self.db.commit()

    def delete_user(self, current_user: UserBase):
        user = self.db.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise NotFoundException(detail="auth.userNotFound")
        user.deleted_at = datetime.now()
        self.db.add(user)
        self.db.flush()

        team_admin = self.db.exec(
            select(func.count(User.id)).where(
                User.team_id == user.team_id,
                User.team_member_role_code == TeamMemberRoleCode.MANAGER,
                User.deleted_at.is_(None),
            )
        ).first()

        if team_admin == 0:
            next_admin = self.db.exec(
                select(User)
                .where(
                    User.team_id == user.team_id,
                    User.team_member_role_code == TeamMemberRoleCode.MEMBER,
                    User.deleted_at.is_(None),
                )
                .order_by(User.id)
                .limit(1)
            ).first()
            if next_admin:
                next_admin.team_member_role_code = TeamMemberRoleCode.MANAGER
                self.db.add(next_admin)
        self.db.commit()
