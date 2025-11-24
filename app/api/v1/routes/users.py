from fastapi import APIRouter, Depends, status

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies.authentication import get_current_user, get_user_service
from app.api.v1.schemas.users import (
    UpdateEmailRequest,
    UpdatePasswordRequest,
    UpdatePublicInformationRequest,
    UserBase,
)
from app.api.v1.services.user_sevice import UserService

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.patch("/update-public-information")
def update_public_information(
    request: UpdatePublicInformationRequest,
    current_user: UserBase = Depends(get_current_user()),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_public_information(current_user, request)


@router.patch("/update-password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    request: UpdatePasswordRequest,
    current_user: UserBase = Depends(get_current_user()),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_password(current_user, request)


@router.patch("/update-email", status_code=status.HTTP_204_NO_CONTENT)
def update_email(
    request: UpdateEmailRequest,
    current_user: UserBase = Depends(get_current_user()),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_email(current_user, request)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    current_user: UserBase = Depends(get_current_user()),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.delete_user(current_user)
