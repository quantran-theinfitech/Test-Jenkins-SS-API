import email.utils as utils
import smtplib
from email.message import EmailMessage
from typing import List, Optional

from sqlmodel import Session, select

from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.mautic_campaign import SequenceMauticCampaign
from app.models.sequence.mautic_event_step import SequenceMauticEventStep
from app.models.sequence.mautic_person import SequenceMauticPerson
from app.models.sequence.mautic_segment import SequenceMauticSegment
from app.models.sequence.step import SequenceCampaignStep, StepType
from external.mautic import MauticService
from external.mautic.schema.campaign import MauticEditCampaignInput


def mautic_create_campaign(db: Session, campaign: SequenceCampaign, order: int):
    mautic_service = MauticService()

    # Add empty segment
    mautic_segment_id = mautic_service.create_segment()

    # Add empty campaign with segment above
    mautic_campaign = mautic_service.create_campaign(campaign, mautic_segment_id)

    sequence_mautic_campaign = SequenceMauticCampaign(
        sequence_campaign_id=campaign.id,
        external_mautic_campaign_id=mautic_campaign.id,
        order=order,
    )
    sequence_segment = SequenceMauticSegment(
        sequence_campaign_id=campaign.id,
        external_mautic_segment_id=mautic_segment_id,
        external_mautic_campaign_id=mautic_campaign.id,
    )
    db.add(sequence_segment)
    db.add(sequence_mautic_campaign)
    db.flush()
    db.refresh(sequence_segment)
    db.refresh(sequence_mautic_campaign)

    return sequence_mautic_campaign, sequence_segment


def mautic_edit_campaign(db: Session, campaign: SequenceCampaign):
    sequence_mautic_campaign = db.exec(
        select(SequenceMauticCampaign)
        .where(SequenceMauticCampaign.sequence_campaign_id == campaign.id)
        .order_by(SequenceMauticCampaign.order.asc())
    ).first()
    segment = db.exec(
        select(SequenceMauticSegment).where(
            SequenceMauticSegment.external_mautic_campaign_id
            == sequence_mautic_campaign.external_mautic_campaign_id
        )
    ).first()
    data = db.exec(
        select(
            SequenceCampaignStep,
            SequenceStepContentTemplate.external_mautic_mail_template_id,
            SequenceMauticEventStep.external_mautic_event_id,
        )
        .join(
            SequenceStepContentTemplate,
            SequenceStepContentTemplate.id == SequenceCampaignStep.content_template_id,
        )
        .join(
            SequenceMauticEventStep,
            SequenceMauticEventStep.sequence_campaign_step_id
            == SequenceCampaignStep.id,
            isouter=True,
        )
        .where(
            SequenceCampaignStep.sequence_campaign_id == campaign.id,
            SequenceCampaignStep.deleted_at.is_(None),
        )
        .order_by(SequenceCampaignStep.order.asc())
    ).all()

    if len(data) == 0:
        return None

    edit_campaign_input = {}
    mautic_event_mapping = {}
    order = sequence_mautic_campaign.order
    for v in data:
        step, mail_template_id, event_id = v
        if event_id:
            mautic_event_mapping[step.uuid] = True
        if step.step_type == StepType.MAIL_MANUAL:
            next_campaign = db.exec(
                select(SequenceMauticCampaign)
                .where(SequenceMauticCampaign.sequence_campaign_id == campaign.id)
                .where(SequenceMauticCampaign.order > order)
                .order_by(SequenceMauticCampaign.order.asc())
            ).first()
            if not next_campaign:
                sequence_mautic_campaign, segment = mautic_create_campaign(
                    db, campaign, order + 1
                )
            else:
                sequence_mautic_campaign = next_campaign
                segment = db.exec(
                    select(SequenceMauticSegment).where(
                        SequenceMauticSegment.external_mautic_campaign_id
                        == sequence_mautic_campaign.external_mautic_campaign_id
                    )
                ).first()
            order += 1

        if not step.is_active:
            continue
        item = MauticEditCampaignInput(**dict(step))
        item.external_mautic_event_id = event_id
        item.external_mautic_mail_template_id = mail_template_id
        if not edit_campaign_input.get(sequence_mautic_campaign.id):
            edit_campaign_input[sequence_mautic_campaign.id] = {
                "mautic_campaign_id": sequence_mautic_campaign.external_mautic_campaign_id,
                "input": [],
                "segment_id": segment.external_mautic_segment_id,
            }
        edit_campaign_input[sequence_mautic_campaign.id]["input"].append(item)

    mautic_service = MauticService()
    for _, data in edit_campaign_input.items():
        mautic_campaign = mautic_service.edit_campaign(
            campaign,
            data["mautic_campaign_id"],
            data["segment_id"],
            data["input"],
        )

        event_mapping = {e.uuid: e.id for e in data["input"]}

        for event in mautic_campaign.events:
            if mautic_event_mapping.get(event.name):
                continue
            db.add(
                SequenceMauticEventStep(
                    sequence_campaign_step_id=event_mapping[event.name],
                    external_mautic_event_id=event.id,
                    external_mautic_campaign_id=data["mautic_campaign_id"],
                )
            )


def mautic_create_batch_contacts(
    db: Session, contacts: List[SequenceContact], campaign_id: int
):
    mautic_service = MauticService()

    mautic_contacts = mautic_service.create_contacts(contacts)

    contact_mapping = {c.uuid: c for c in contacts if c is not None}
    for contact in mautic_contacts:
        if not contact_mapping.get(contact.uuid):
            print(f"Contact {contact.uuid} not found in mapping")
            continue
        db.add(
            SequenceMauticPerson(
                external_mautic_person_id=contact.mautic_contact_id,
                sequence_person_id=contact_mapping[contact.uuid].id,
            )
        )
        db.flush()

    mautic_segment = db.exec(
        select(SequenceMauticSegment).where(
            SequenceMauticSegment.sequence_campaign_id == campaign_id
        )
    ).first()
    mautic_service.add_contact_to_segment(
        [c.mautic_contact_id for c in mautic_contacts],
        mautic_segment.external_mautic_segment_id,
    )


def mautic_delete_contact(db: Session, contact: SequenceContact):
    mautic_person = db.exec(
        select(SequenceMauticPerson).where(
            SequenceMauticPerson.sequence_person_id == contact.id
        )
    ).first()
    if not mautic_person:
        return
    mautic_service = MauticService()
    mautic_service.delete_contact(mautic_person.external_mautic_person_id)
    db.delete(mautic_person)
    db.commit()


async def send_email(
    mailbox: SequenceMailbox,
    subject,
    content,
    email_to,
    msg_id: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
):
    message = EmailMessage()
    message.set_content(content, subtype="html")
    message["From"] = mailbox.email
    message["To"] = email_to
    message["Subject"] = subject
    mesage_id = utils.make_msgid(domain="app.salessmart.jp")
    message["Message-ID"] = mesage_id
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    if msg_id:
        message["In-Reply-To"] = msg_id
        message["References"] = msg_id
    else:
        message["References"] = mesage_id
    with smtplib.SMTP(mailbox.host, mailbox.port) as server:
        server.starttls()
        server.login(mailbox.email, mailbox.password)
        try:
            server.send_message(message)
        except Exception as e:
            raise e

    return message
