from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.models.export_history import ExportHistory, ExportStatus
from app.models.user import User
from external.s3 import S3Service


def download_file_by_export_history_id_service(
    db: Session,
    current_user: User,
    export_history_id: int,
):
    export_history = db.exec(
        select(ExportHistory).where(
            ExportHistory.team_id == current_user.team_id,
            ExportHistory.id == export_history_id,
            ExportHistory.deleted_at.is_(None),
            ExportHistory.status == ExportStatus.AVAILABLE,
        )
    ).first()

    if not export_history:
        raise NotFoundException(deatil="export.notfound")

    # Retrieve the file from S3
    s3_service = S3Service()

    s3_file_content = s3_service.get_object(export_history.file_name)

    filename = export_history.file_name.split("/")[
        -1
    ]  # Extract the file name from the S3 path

    return StreamingResponse(
        s3_file_content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename.encode('utf-8').decode('latin-1')}"
        },  # Ensure filename is properly encoded
    )
