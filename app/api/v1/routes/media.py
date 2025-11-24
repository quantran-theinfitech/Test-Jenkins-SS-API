from fastapi import APIRouter, Depends, Query

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.media import PresignedUploadUrlResponse, PresignedUrlResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services import media as media_service
from app.constant.constants import MediaCategory
from utils.media_utils import set_media_filename

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/presigned-get-url",
    response_model=PresignedUrlResponse,
)
def get_presigned_url(
    presigned_key: str = Query(
        ..., description="The presigned key to get the presigned url"
    ),
):
    get_presigned_url = media_service.get_presigned_url(presigned_key)

    return PresignedUrlResponse(
        url=get_presigned_url,
    )


@router.get(
    "/{category}/presigned-upload-url",
    response_model=PresignedUploadUrlResponse,
)
def get_presigned_upload_url(
    category: MediaCategory,
    current_user: UserBase = Depends(get_current_user()),
):
    object_name = set_media_filename(category, True)
    upload_presigned_url = media_service.generate_presigned_upload_url(object_name)
    get_presigned_url = media_service.get_presigned_url(object_name)

    return PresignedUploadUrlResponse(
        upload_url=upload_presigned_url,
        get_url=get_presigned_url,
        path=object_name,
    )
