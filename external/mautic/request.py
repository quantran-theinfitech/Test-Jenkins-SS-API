import re
import uuid
from typing import List

from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.contact import SequenceContact
from app.models.sequence.step import StepType, TimingType
from external.mautic.schema.campaign import (
    BASE_STEP_ID,
    SS_TRIGGER_INTERVAL_UNIT_MAPPING,
    Anchor,
    AnchorType,
    CanvasSetting,
    Connection,
    EmailType,
    EventType,
    MauticCampaign,
    MauticCampaignEvent,
    MauticEditCampaignInput,
    Property,
    TriggerMode,
    Type,
)
from external.mautic.schema.mail_template import (
    MauticMailTemplate,
    Template,
    TemplateEmailType,
)
from external.mautic.schema.person import SS_FIELD_MAPPING


def default_mautic_campaign_request(
    campaign: SequenceCampaign, segment_id: int
) -> MauticCampaign:
    req = MauticCampaign()
    req.name = campaign.name
    req.description = "Created by SS"
    req.isPublished = False
    req.lists = [{"id": segment_id}]
    event = MauticCampaignEvent(
        id="new_99999",
        name="default event",
        description="default event",
        triggerMode=TriggerMode.IMMEDIATE,
        eventType=EventType.CONDITION,
        type=Type.VALID_EMAIL_CHECK,
        order=1,
    )
    connection = Connection(
        anchors=Anchor(
            source=(AnchorType.LEAD_SOURCE),
            target=AnchorType.TOP,
        ),
        sourceId=BASE_STEP_ID,
        targetId=event.id,
    )
    req.events.append(event)
    req.canvasSettings = CanvasSetting(
        connections=[connection],
    )
    return req


def make_mautic_campaign_request(
    campaign: SequenceCampaign,
    segment_id: int,
    data: List[MauticEditCampaignInput],
) -> MauticCampaign:
    req = MauticCampaign()
    req.name = f"{campaign.name}-{segment_id}"
    req.description = "Created by SS"
    req.isPublished = campaign.is_active
    req.lists = [{"id": segment_id}]
    connections = []
    previous_step_id = BASE_STEP_ID
    for e in data:
        event_id = (
            f"new_{e.id}"
            if e.external_mautic_event_id is None
            else e.external_mautic_event_id
        )
        event = MauticCampaignEvent()
        event.id = event_id
        event.name = e.uuid
        event.description = e.description
        event.type = Type.SEND_EMAIL
        event.eventType = EventType.ACTION
        event.properties = Property(
            email=e.external_mautic_mail_template_id,
            email_type=EmailType.TRANSACTIONAL,
        )
        event.order = e.order
        event.triggerMode = TriggerMode.IMMEDIATE
        if e.step_type == StepType.MAIL_AUTO and e.timing_type == TimingType.SCHEDULED:
            event.triggerMode = TriggerMode.INTERVAL
            event.triggerInterval = e.schedule_value
            event.triggerIntervalUnit = SS_TRIGGER_INTERVAL_UNIT_MAPPING.get(
                e.schedule_unit
            )
        connection = Connection(
            anchors=Anchor(
                source=(
                    AnchorType.LEAD_SOURCE
                    if previous_step_id == BASE_STEP_ID
                    else AnchorType.BOTTOM
                ),
                target=AnchorType.TOP,
            ),
            sourceId=previous_step_id,
            targetId=event.id,
        )
        connections.append(connection)
        req.events.append(event)
        previous_step_id = event.id
    req.canvasSettings = CanvasSetting(
        connections=connections,
    )

    return req


def make_mautic_contacts_request(contacts: List[SequenceContact]) -> List:
    data = []
    for contact in contacts:
        item = {}
        for k, v in SS_FIELD_MAPPING.items():
            if not getattr(contact, v):
                continue
            # fake email with uuid
            item[k] = getattr(contact, v)
            if k == "email":
                item[k] = f"{getattr(contact, v)}@fakedomain.com"
        data.append(item)
    return data


def make_mautic_mail_request(subject, content) -> MauticMailTemplate:
    if not content or content == "":
        content = "<p></p>"
    for k, v in SS_FIELD_MAPPING.items():
        content = re.sub(f"{{{{{v}}}}}", f"{{contactfield={k}}}", content)
    return MauticMailTemplate(
        name=str(uuid.uuid4()),
        subject=subject,
        plainText=content,
        customHtml=content,
        emailType=TemplateEmailType.TEMPLATE,
        template=Template.MAUTIC_CODE_MODE,
        isPublished=True,
    )
