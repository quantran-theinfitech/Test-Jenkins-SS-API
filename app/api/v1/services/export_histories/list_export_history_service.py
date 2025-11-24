from sqlmodel import Session, func, select

from app.models.export_history import ExportHistory
from app.models.user import User


def list_export_history_service(
    db: Session,
    current_user: User,
    page: int,
    per_page: int,
):
    query = select(ExportHistory).where(
        ExportHistory.team_id == current_user.team_id,
        ExportHistory.deleted_at.is_(None),
    )

    export_histories = db.exec(
        query.offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(ExportHistory.created_at.desc())
    ).all()

    total = (
        db.execute(query.with_only_columns(func.count(ExportHistory.id))).scalar() or 0
    )

    return export_histories, total
