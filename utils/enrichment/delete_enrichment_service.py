from sqlmodel import Session, delete, select

from app.models.enrichment_file import EnrichmentFile
from app.models.enrichment_item import EnrichmentItem
from app.models.enrichment_item_data import EnrichmentItemData


def delete_all_file_in_enrichment(
    enrichment_id: int,
    db: Session,
):
    db.exec(
        delete(EnrichmentItemData)
        .where(
            EnrichmentItemData.enrichment_item_id.in_(
                select(EnrichmentItem.id).where(
                    EnrichmentItem.enrichment_id == enrichment_id
                )
            )
        )
        .execution_options(synchronize_session=False)
    )
    db.exec(
        delete(EnrichmentItem)
        .where(EnrichmentItem.enrichment_id == enrichment_id)
        .execution_options(synchronize_session=False)
    )
    db.exec(
        delete(EnrichmentFile)
        .where(EnrichmentFile.enrichment_id == enrichment_id)
        .execution_options(synchronize_session=False)
    )
    db.flush()
    return True
