from functools import partial

import sentry_sdk
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlmodel import Session

from app.api.base.deps import get_session
from app.api.base.exceptions import NotFoundException, UnauthorizedException
from app.api.v1.schemas.users import TokenPayload
from app.api.v1.services.user_sevice import AuthService, UserService
from app.config import settings

user_oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


def get_user_service(db: Session = Depends(get_session)):
    return UserService(db)


def get_current_user(confirm_policy: bool = False, raise_exception: bool = True):
    if confirm_policy is False:
        return partial(get_current_user_impl, raise_exception)
    else:
        return partial(get_current_user_impl, raise_exception, confirm_policy)


def get_current_user_with_no_pw(raise_exception: bool = True):
    return partial(get_current_user_with_no_pw_impl, raise_exception)


def get_current_user_with_no_pw_impl(
    raise_exception: bool = True,
    token: str = Depends(user_oauth2),
    user_service: UserService = Depends(get_user_service),
):
    if token:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError):
            if raise_exception:
                raise UnauthorizedException(detail="auth.couldNotValidateCredentials")
            return None
        if token_data.init_password is not True:
            if raise_exception:
                raise UnauthorizedException(detail="auth.couldNotValidateCredentials")
            return None
        user = user_service.get_user_by_email(token_data.sub)

        if not user:
            if raise_exception:
                raise NotFoundException(detail="auth.userNotFound")
            return None
        return user
    else:
        if raise_exception:
            raise UnauthorizedException(detail="auth.couldNotValidateCredentials")
        return None


def get_auth_service(db: Session = Depends(get_session)):
    return AuthService(db)


def get_current_user_impl(
    raise_exception: bool,
    confirm_policy: bool = False,
    token: str = Depends(user_oauth2),
    user_service: UserService = Depends(get_user_service),
):
    if token:

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError):
            if raise_exception:
                raise UnauthorizedException(detail="auth.couldNotValidateCredentials")
            return None
        if token_data.init_password is True:
            if raise_exception:
                raise UnauthorizedException(detail="auth.couldNotValidateCredentials")
            return None
        user = user_service.get_user_by_email(token_data.sub)

        if not user:
            if raise_exception:
                raise NotFoundException(detail="auth.userNotFound")
            return None

        if user.deleted_at:
            if raise_exception:
                raise UnauthorizedException(detail="auth.userDeleted")
            return None

        if (
            user.password_updated_at
            and user.password_updated_at.isoformat() != token_data.password_updated_at
        ):

            if raise_exception:
                raise UnauthorizedException(detail="auth.passwordUpdated")
            return None

        if confirm_policy is False and user.flag_first_login and raise_exception:
            raise UnauthorizedException(detail="auth.requirePolicyAgreementMessage")
        sentry_sdk.set_user(
            {
                "id": user.id,
                "email": user.email,
            }
        )
        return user
    else:
        if raise_exception:
            raise UnauthorizedException(detail="auth.couldNotValidateCredentials")
        return None


def get_message_from_token():
    return partial(get_message_from_token_impl)


def get_message_from_token_impl(token: str = Depends(user_oauth2)):
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError):
            raise UnauthorizedException(detail="auth.couldNotValidateCredentials")

        return token_data.sub
    else:
        raise UnauthorizedException(detail="auth.couldNotValidateCredentials")
