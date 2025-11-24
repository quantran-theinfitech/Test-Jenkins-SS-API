# flake8: noqa: C901
from datetime import datetime

from sqlmodel import Session, delete, or_, select, update

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.campaigns import UpdateCampaignPersonsRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory
from app.models.sequence.task import SequenceTask


def update_campaign_persons_service(
    db: Session,
    current_user: UserBase,
    campaign_id: int,
    request: UpdateCampaignPersonsRequest,
):
    result = True  # True: all contacts finished or bounced, False: some contacts not finished
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.deleted_at.is_(None),
        )
    ).first()
    if not campaign:
        raise NotFoundException("Campaign not found")

    updated_person_ids = []

    if request.sequence_person_ids:
        campaign_persons = db.exec(
            select(SequenceCampaignContacts).where(
                SequenceCampaignContacts.sequence_campaign_id == campaign_id,
                SequenceCampaignContacts.sequence_contact_id.in_(
                    request.sequence_person_ids
                ),
            )
        ).all()

        for campaign_person in campaign_persons:
            if (
                campaign_person.status != StatusEnum.FINISH
                and campaign_person.status != StatusEnum.BOUNCED
            ):
                result = False
                if request.time_resumed:
                    campaign_person.time_resumed = request.time_resumed
                else:
                    campaign_person.time_resumed = None
                if (
                    campaign_person.status == StatusEnum.PAUSE
                    and request.status == StatusEnum.ACTIVE
                ):
                    campaign_person.time_resumed = datetime.now()
                if (
                    campaign_person.status == StatusEnum.ACTIVE
                    and request.status == StatusEnum.ACTIVE
                ):
                    campaign_person.time_resumed = datetime.now()
                campaign_person.status = request.status
                if (
                    request.status == StatusEnum.FINISH.value
                    or request.status == StatusEnum.PAUSE.value
                ):
                    # db.exec(
                    #     update(SequenceMailHistory)
                    #     .where(
                    #         SequenceMailHistory.sequence_contact_id
                    #         == campaign_person.sequence_contact_id,
                    #         or_(
                    #             SequenceMailHistory.status
                    #             == MailHistoryStatus.SCHEDULED,
                    #             SequenceMailHistory.status == MailHistoryStatus.FAILED,
                    #         ),
                    #     )
                    #     .values(
                    #         deleted_at=datetime.now(),
                    #         deleted_by=current_user.id,
                    #     )
                    # )
                    db.exec(
                        delete(SequenceMailHistory).where(
                            SequenceMailHistory.sequence_contact_id
                            == campaign_person.sequence_contact_id,
                            SequenceMailHistory.deleted_at.is_(None),
                            or_(
                                SequenceMailHistory.status
                                == MailHistoryStatus.SCHEDULED,
                                # SequenceMailHistory.status == MailHistoryStatus.FAILED,
                            ),
                        )
                    )
                    db.exec(
                        update(SequenceTask)
                        .where(
                            SequenceTask.sequence_person_id
                            == campaign_person.sequence_contact_id,
                            SequenceTask.deleted_at.is_(None),
                            SequenceTask.sequence_campaign_id == campaign_id,
                        )
                        .values(
                            deleted_at=datetime.now(),
                            deleted_by=current_user.id,
                        )
                    )
                campaign_person.updated_by = current_user.id
                campaign_person.updated_at = datetime.now()
                campaign_person.reason = request.reason
                updated_person_ids.append(campaign_person.sequence_contact_id)

        db.commit()

    return result
