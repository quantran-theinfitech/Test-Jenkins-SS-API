from typing import List, Tuple

from sqlmodel import Session, and_, exists, func, or_, select

from app.api.v1.schemas.enrichments import (
    EnrichmentListItemResponse,
    EnrichmentListQueryParams,
)
from app.models.enrichment import Enrichment
from app.models.enrichment_file import EnrichmentFile


def _build_condition(query_params: EnrichmentListQueryParams):
    conditions = []
    if query_params.keyword:
        conditions.append(
            or_(
                Enrichment.name.contains(query_params.keyword),
                exists().where(
                    and_(
                        EnrichmentFile.enrichment_id == Enrichment.id,
                        EnrichmentFile.file_name.contains(query_params.keyword),
                        EnrichmentFile.deleted_at.is_(None),
                    )
                ),
            )
        )
    return conditions


def _get_total_enrichments(
    db: Session,
    team_id: int,
    conditions: list,
):
    count_query = select(func.count(Enrichment.id)).where(
        Enrichment.team_id == team_id,
        Enrichment.deleted_at.is_(None),
        *conditions,
    )
    return db.exec(count_query).first()


def list_enrichments(
    db: Session,
    team_id: int,
    query_params: EnrichmentListQueryParams,
) -> Tuple[List[EnrichmentListItemResponse], int]:
    conditions = _build_condition(query_params)
    total = _get_total_enrichments(db, team_id, conditions)

    enrichments_query = (
        select(Enrichment)
        .where(
            Enrichment.team_id == team_id,
            Enrichment.deleted_at.is_(None),
            *conditions,
        )
        .order_by(Enrichment.id.desc())
    )

    if not query_params.get_all:
        enrichments_query = enrichments_query.offset(
            (query_params.page - 1) * query_params.per_page
        ).limit(query_params.per_page)

    enrichments = db.exec(enrichments_query).all()

    enrichment_ids = [e.id for e in enrichments]
    if enrichment_ids:
        files_query = (
            select(EnrichmentFile)
            .where(
                EnrichmentFile.enrichment_id.in_(enrichment_ids),
                EnrichmentFile.deleted_at.is_(None),
            )
            .order_by(EnrichmentFile.enrichment_id, EnrichmentFile.created_at.desc())
        )
        files = db.exec(files_query).all()
    else:
        files = []

    files_by_enrichment = {}
    for file in files:
        files_by_enrichment.setdefault(file.enrichment_id, []).append(file)

    enrichment_responses = []
    for enrichment in enrichments:
        enrichment_response = EnrichmentListItemResponse(
            id=enrichment.id,
            team_id=enrichment.team_id,
            name=enrichment.name,
            enrichment_file=files_by_enrichment.get(enrichment.id, []),
            status=enrichment.status,
        )
        enrichment_responses.append(enrichment_response)

    return enrichment_responses, total
