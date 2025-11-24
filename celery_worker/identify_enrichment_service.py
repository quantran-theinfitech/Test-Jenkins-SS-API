from sqlmodel import Session

from app.models.enrichment import Enrichment
from utils.identify.identify_enrichment_service import identify_enrichment_file


def identify_enrichment_service(
    enrichment_id: int,
    user_id: int,
    item_id_list,
    is_last_chunk,
    enrichment_file_id,
    db: Session,
):
    print(f"Start identifying enrichment {enrichment_id}.")
    enrichment = db.get(Enrichment, enrichment_id)
    identify_enrichment_file(
        db, enrichment, user_id, enrichment_file_id=enrichment_file_id
    )
    print(f"Finish identifying enrichment {enrichment_id}.")
    return True
