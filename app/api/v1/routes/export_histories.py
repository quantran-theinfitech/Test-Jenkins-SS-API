from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.export_histories import ListExportHistoryResponse
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.services.export_histories.download_export_history_service import (
    download_file_by_export_history_id_service,
)
from app.api.v1.services.export_histories.list_export_history_service import (
    list_export_history_service,
)
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=ListExportHistoryResponse)
def listing_all_export_histories(
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    current_user: User = Depends(get_current_user()),
):
    data, total = list_export_history_service(db, current_user, page, per_page)
    return ListExportHistoryResponse(
        data=data, total=total, page=page, per_page=per_page
    )


@router.post(
    "/download/{export_history_id}",
    response_class=StreamingResponse,
)
def download_file_by_export_history_id(
    export_history_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user()),
):
    return download_file_by_export_history_id_service(
        db, current_user, export_history_id
    )
