from sqlmodel import Session, select

from app.api.v1.schemas.sequence.persons import CampaignImportBase, CampaignImportList
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.campaign_import import SequenceCampaignImport
from app.models.user import User


def get_sequence_campaign_imports_service(
    sequence_campaign_id: int, db: Session, current_user: User
) -> CampaignImportList:
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    imports = db.exec(
        select(SequenceCampaignImport)
        .where(
            SequenceCampaignImport.sequence_campaign_id == sequence_campaign_id,
            SequenceCampaignImport.team_id == current_user.team_id,
            SequenceCampaignImport.deleted_at.is_(None),
        )
        .order_by(SequenceCampaignImport.created_at.desc())
    ).all()

    return CampaignImportList(
        data=[
            CampaignImportBase(
                sequence_campaign_import_id=import_record.id,
                sequence_campaign_import_name=import_record.name,
            )
            for import_record in imports
        ]
    )
