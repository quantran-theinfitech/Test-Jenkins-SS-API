from typing import List

from fastapi import APIRouter, Depends

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import get_activity_logs_service, get_current_user
from app.api.v1.schemas.activity_logs import ActivityLogBase
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.activity_logs_service import ActivityLogsService

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "",
    response_model=List[ActivityLogBase],
    operation_id="listing_activity_logs",
)
def listing_activity_logs(
    corporate_number: str,
    activity_logs_sevice: ActivityLogsService = Depends(get_activity_logs_service),
    current_user: UserBase = Depends(get_current_user()),
):
    return activity_logs_sevice.listing_activity_logs(current_user, corporate_number)
