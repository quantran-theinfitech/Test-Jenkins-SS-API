import i18n
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi_mail import ConnectionConfig
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, mail_connection
from app.api.v1.dependencies import (
    check_active_platform,
    get_auth_service,
    get_current_user,
    get_current_user_with_no_pw,
    get_plan_code,
    get_user_service,
)
from app.api.v1.dependencies.credit import get_platform
from app.api.v1.schemas.users import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    ConfirmPolicyResponse,
    CreateUserRequest,
    CreateUserResponse,
    GetUserResponse,
    RefreshToken,
    RegisterRequest,
    RegisterResponse,
    Token,
    UserBase,
    UserLoginRequest,
    VerifyTokenResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.api.v1.services import media as media_service
from app.api.v1.services.user_sevice import AuthService, UserService
from app.models.plan import PlanServiceCode
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


def __init__(self, db: Session):
    self.db = db


@router.post("/login", response_model=Token)
def login(
    form_data: UserLoginRequest,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.login_for_access_token(form_data)


@router.patch("/confirm-policy", response_model=ConfirmPolicyResponse)
def confirm_policy(
    current_user: UserBase = Depends(get_current_user(True)),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.confirm_policy(current_user)


@router.patch("/hide-tutorial")
def hide_tutorial(
    current_user: UserBase = Depends(get_current_user(True)),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.hide_tutorial(current_user)


@router.post("/register", response_model=RegisterResponse)
def register(
    form_data: RegisterRequest,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.register(form_data)


@router.post("/send-verification-email", response_model=CreateUserResponse)
async def send_verification_email(
    form_data: CreateUserRequest,
    user_service: UserService = Depends(get_user_service),
    mail_connection: ConnectionConfig = Depends(mail_connection),
):
    return await user_service.send_verification_email(form_data, mail_connection)

@router.post("/reset-password/send-verification-email", response_model=CreateUserResponse)
async def send_verification_email_for_forgot_password(
    form_data: CreateUserRequest,
    user_service: UserService = Depends(get_user_service),
    mail_connection: ConnectionConfig = Depends(mail_connection),
):
    return await user_service.send_verification_email_for_forgot_password(form_data, mail_connection)

@router.get("/me", response_model=GetUserResponse)
def get_user_detail(
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    form_plan_code: PlanCode = Depends(get_plan_code(PlanServiceCode.FORM)),
    active_platform: bool = Depends(check_active_platform()),
    platform: str = Depends(get_platform()),
):
    return GetUserResponse(
        id=current_user.id,
        role_code=current_user.role_code,
        team_member_role_code=current_user.team_member_role_code,
        team_id=current_user.team_id,
        email=current_user.email,
        name=current_user.name,
        gender_code=current_user.gender_code,
        linkedin_profile_url=current_user.linkedin_profile_url,
        listing_plan_code=listing_plan_code,
        form_plan_code=form_plan_code,
        active_platform=active_platform,
        platform=platform,
        avatar_path=media_service.get_presigned_url(current_user.avatar_path),
    )


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    input_token_refresh: RefreshToken,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    return user_service.refresh_token(input_token_refresh, auth_service)


@router.post("/logout")
def logout():
    return HTMLResponse(status_code=204)


@router.patch("/change-password", response_model=ChangePasswordResponse)
def change_password(
    change_password_form: ChangePasswordRequest,
    user_service: UserService = Depends(get_user_service),
    current_user: UserBase = Depends(get_current_user()),
):
    user_service.change_password(current_user, change_password_form.password)
    return ChangePasswordResponse(detail=i18n.t("auth.resetPasswordSuccess"))


@router.patch("/create-password", response_model=ChangePasswordResponse)
def create_password(
    change_password_form: ChangePasswordRequest,
    user_service: UserService = Depends(get_user_service),
    current_user: UserBase = Depends(get_current_user_with_no_pw()),
):
    user_service.change_password(current_user, change_password_form.password)
    user_service.verify_email(current_user)
    return ChangePasswordResponse(detail="auth.createPasswordSuccess")


@router.get("/verify-token", response_model=VerifyTokenResponse)
def verify_token(token: str, user_service: UserService = Depends(get_user_service)):
    return VerifyTokenResponse(email=user_service.verify_token(token))

@router.get("/reset-password/verify-token", response_model=VerifyTokenResponse)
def verify_token_for_reset_password(token: str, user_service: UserService = Depends(get_user_service)):
    return VerifyTokenResponse(email=user_service.verify_token_for_reset_password(token))

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(reset_password_form: ResetPasswordRequest, user_service: UserService = Depends(get_user_service)):
    return user_service.reset_password(reset_password_form.token, reset_password_form.password)