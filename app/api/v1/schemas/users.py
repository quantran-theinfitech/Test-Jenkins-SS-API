from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import GenderCode


class RegisterRequestContent(BaseModel):
    company_name: str
    position_code: str
    department_name: Optional[str] = None
    name: str
    email: str
    password: str
    tel: Optional[str] = None
    expect_meeting_flag: Optional[int] = None
    gender_code: Optional[GenderCode] = None
    linkedin_profile_url: Optional[str] = None


class RegisterRequest(BaseModel):
    token: str
    content: RegisterRequestContent
    invitation_token: Optional[str] = None


class CreateUserRequest(BaseModel):
    email: EmailStr


class VerifyTokenResponse(CreateUserRequest):
    pass


class UserBase(BaseModel):
    id: Optional[int] = None
    role_code: Optional[str] = None
    team_member_role_code: Optional[str] = None
    team_id: Optional[int] = None
    email: str
    name: Optional[str] = None
    gender_code: Optional[GenderCode] = None
    linkedin_profile_url: Optional[str] = None
    flag_first_login: Optional[bool] = False
    avatar_path: Optional[str] = None
    deleted_at: Optional[datetime] = None
    password_updated_at: Optional[datetime] = None


class GetUserResponse(UserBase):
    listing_plan_code: str
    form_plan_code: str
    active_platform: Optional[bool] = None
    platform: Optional[str] = None


class RegisterResponse(UserBase):
    pass


class CreateUserResponse(BaseModel):
    expired_at: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class ConfirmPolicyResponse(UserBase):
    pass


class Token(BaseModel):
    token_type: str
    access_token: str
    expire_at: datetime
    refresh_token: str
    refresh_expire_at: datetime
    flag_first_login: Optional[bool] = None
    show_tutorial_flag: Optional[bool] = None
    login_with_init_pw: Optional[bool] = None


class TokenPayload(BaseModel):
    exp: datetime
    sub: str
    refresh: Optional[bool]
    listing_plan_code: Optional[str] = None
    form_plan_code: Optional[str] = None
    init_password: Optional[bool] = None
    password_updated_at: Optional[str] = None


class RefreshToken(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    password: str


class ChangePasswordResponse(BaseModel):
    detail: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class ResetPasswordResponse(BaseModel):
    detail: str

class TokenData(BaseModel):
    email: str
    iat: datetime
    exp: datetime


class UpdatePublicInformationRequest(BaseModel):
    name: Optional[str] = None
    avatar_path: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)
    new_password_confirm: str = Field(min_length=1)
    force_logout: Optional[bool] = False


class UpdateEmailRequest(BaseModel):
    new_email: EmailStr = Field(..., description="New email to update")
    password: str = Field(min_length=1)
