import re

from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.models.enrichment import Enrichment


def file_compatible_check(
    columns: list,
    enrichment_id: int,
    db: Session,
):
    enrichment = db.exec(
        select(Enrichment).where(
            Enrichment.id == enrichment_id,
            Enrichment.deleted_at.is_(None),
        )
    ).first()
    if not enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")
    upload_columns = []
    for k, v in enrichment.column_json_mapping.items():
        upload_columns.append(v.get("upload_column", None))
    if len(upload_columns) != len(columns):
        return False
    for index, column in enumerate(columns):
        if column not in upload_columns or upload_columns.index(column) != index:
            return False
    return enrichment


def convert_dot_columns_to_underscore(columns):
    return [re.sub(r"\.(\d+)$", r"_\1", col) for col in columns]
