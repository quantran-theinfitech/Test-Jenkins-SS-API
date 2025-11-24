from datetime import datetime
from typing import Optional, Tuple

from sqlmodel import Session, and_, or_, select, update

from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import SequenceContact, SequencePersonStage
from app.models.sequence.mail_alias import SequenceMailAlias
from app.models.sequence.mail_alias_setting import (
    SequenceMailAliasSetting,
    SettingOption,
)
from app.models.sequence.mail_history import SequenceMailHistory
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.person_statistics import SequencePersonStatistics


def get_mail_alias_setting(
    db: Session,
    campaign_id: int,
    step_id: int,
    person_id: int,
) -> Optional[Tuple[SequenceMailbox, SequenceMailAlias]]:
    return db.exec(
        select(SequenceMailbox, SequenceMailAlias)
        .join(
            SequenceMailAliasSetting,
            SequenceMailbox.id == SequenceMailAliasSetting.mailbox_id,
        )
        .join(
            SequenceMailAlias,
            SequenceMailAlias.id == SequenceMailAliasSetting.mailbox_alias_id,
            isouter=True,
        )
        .where(
            or_(
                and_(
                    SequenceMailAliasSetting.setting_option == SettingOption.STEP,
                    SequenceMailAliasSetting.sequence_campaign_id == campaign_id,
                    SequenceMailAliasSetting.sequence_step_id == step_id,
                    SequenceMailAliasSetting.sequence_person_id == person_id,
                ),
                and_(
                    SequenceMailAliasSetting.setting_option == SettingOption.CONTACT,
                    SequenceMailAliasSetting.sequence_campaign_id == campaign_id,
                    SequenceMailAliasSetting.sequence_person_id == person_id,
                ),
            ),
            SequenceMailbox.deleted_at.is_(None),
        )
        .order_by(SequenceMailAliasSetting.created_at.desc())
    ).first()


def handle_opt_out_contact(db: Session, mail_history: SequenceMailHistory):
    result = db.exec(
        select(SequenceContact, SequencePersonStatistics)
        .outerjoin(
            SequencePersonStatistics,
            SequenceContact.id == SequencePersonStatistics.sequence_person_id,
        )
        .where(
            SequenceMailHistory.id == mail_history.id,
            SequenceContact.id == mail_history.sequence_contact_id,
            SequenceContact.deleted_at.is_(None),
        )
    ).first()
    if not result:
        return
    person, person_stats = result
    if not person:
        return
    if person_stats:
        person_stats.last_activity = datetime.now()
    else:
        person_stats = SequencePersonStatistics(
            sequence_person_id=mail_history.sequence_contact_id,
            last_activity=datetime.now(),
        )

    db.add(person_stats)
    db.exec(
        update(SequenceCampaignContacts)
        .where(
            SequenceCampaignContacts.sequence_contact_id
            == mail_history.sequence_contact_id,
            SequenceCampaignContacts.sequence_campaign_id
            == mail_history.sequence_campaign_id,
        )
        .values(status=StatusEnum.FINISH.value)
    )
    person.stage = SequencePersonStage.DO_NOT_CONTACT
    db.add(person)
