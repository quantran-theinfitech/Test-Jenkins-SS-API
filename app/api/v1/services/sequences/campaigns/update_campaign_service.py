from datetime import datetime
from typing import List

from sqlmodel import Session, delete, select, update

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.sequence.campaigns import (
    UpdateCampaignRequest,
    UpdateCampaignResponse,
    UpdateStepRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.linkedin_account import LinkedInAccount, LinkedInAccountStatus
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.sequence.task import SequenceTask
from app.models.team import PlanCode, Team
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit

from .get_sequence_campaign_step_service import get_total_days_count


def update_campaign_service(
    db: Session,
    current_user: UserBase,
    campaign_id: int,
    request: UpdateCampaignRequest,
    listing_plan_code: PlanCode,
):
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).first()

    if not campaign:
        raise NotFoundException("Campaign not found")

    if request.is_active is True and campaign.is_active is False:
        campaign.activated_at = datetime.now()
        if campaign.is_first_active is False:
            campaign.is_first_active = True

        account_linkedin = (
            db.query(LinkedInAccount)
            .filter(
                LinkedInAccount.team_id == campaign.team_id,
                LinkedInAccount.is_default.is_(True),
                LinkedInAccount.deleted_at.is_(None),
            )
            .first()
        )

        if not account_linkedin or (
            account_linkedin
            and account_linkedin.status != LinkedInAccountStatus.CREDENTIALS
        ):
            db.exec(
                update(SequenceCampaignContacts)
                .where(
                    SequenceCampaignContacts.sequence_campaign_id == campaign.id,
                    SequenceCampaignContacts.status == "PAUSE",
                    SequenceCampaignContacts.deleted_at.is_(None),
                )
                .values(status="ACTIVE", time_resumed=datetime.now())
            )

    if request.is_active is False:
        campaign.activated_at = None
        db.exec(
            update(SequenceCampaignContacts)
            .where(
                SequenceCampaignContacts.sequence_campaign_id == campaign.id,
                SequenceCampaignContacts.status == "ACTIVE",
                SequenceCampaignContacts.deleted_at.is_(None),
            )
            .values(status="PAUSE", time_resumed=None)
        )
        db.exec(
            delete(SequenceMailHistory).where(
                SequenceMailHistory.sequence_campaign_id == campaign_id,
                SequenceMailHistory.deleted_at.is_(None),
                SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
            )
        )

    for attr, value in request.dict(exclude_unset=True).items():
        setattr(campaign, attr, value)
    campaign.updated_by = current_user.id
    campaign.updated_at = datetime.now()
    db.add(campaign)
    db.flush()
    db.refresh(campaign)

    db.commit()
    return campaign.id


def check_mailbox_exist(db: Session, current_user: UserBase):
    current_team = db.get(Team, current_user.team_id)
    mailbox_id = db.exec(
        select(SequenceMailbox.id).where(
            SequenceMailbox.deleted_at.is_(None),
            SequenceMailbox.team_id == current_team.id,
        )
    ).first()
    return mailbox_id is not None


def check_linkedin_sender_exist(db: Session, current_user: UserBase):
    current_team = db.get(Team, current_user.team_id)
    linkedin_account_id = db.exec(
        select(LinkedInAccount.id).where(
            LinkedInAccount.deleted_at.is_(None),
            LinkedInAccount.team_id == current_team.id,
        )
    ).first()
    return linkedin_account_id is not None


def get_active_campaign_warning_service(
    db: Session,
    current_user: UserBase,
    campaign_id: int,
):
    is_credit_warning = False
    is_mailbox_warning = False
    is_linkedin_warning = False
    campaign_steps = db.exec(
        select(SequenceCampaignStep).where(
            SequenceCampaignStep.sequence_campaign_id == campaign_id,
            SequenceCampaignStep.deleted_at.is_(None),
            # SequenceCampaignStep.is_active == True,
        )
    ).all()
    current_plan_code = db.exec(
        select(Team.listing_plan_code).where(Team.id == current_user.team_id)
    ).first()
    has_mail_steps = any(
        step.step_type in [StepType.MAIL_AUTO, StepType.MAIL_MANUAL]
        for step in campaign_steps
    )
    has_linkedin_steps = any(
        step.step_type
        in [
            StepType.LINKEDIN_AUTO_MESSAGE,
            StepType.LINKEDIN_CONNECTION_REQUEST,
            StepType.LINKEDIN_VIEW_PROFILE,
        ]
        for step in campaign_steps
    )

    if current_plan_code == PlanCode.FRE:
        is_credit_warning = True
    else:
        if (
            not is_enough_credit(db, current_user.team_id, 1, ServiceCode.EMAIL)
            and not has_mail_steps
            and not has_linkedin_steps
        ):
            is_credit_warning = True
        if (
            not is_enough_credit(db, current_user.team_id, 1, ServiceCode.LINKEDIN_MSG)
            and not has_mail_steps
            and not has_linkedin_steps
        ):
            is_credit_warning = True
        if (
            not is_enough_credit(db, current_user.team_id, 1, ServiceCode.EMAIL)
            and has_mail_steps
        ):
            is_credit_warning = True
        if (
            not is_enough_credit(db, current_user.team_id, 1, ServiceCode.LINKEDIN_MSG)
            and has_linkedin_steps
        ):
            is_credit_warning = True
        # Check mailbox requirement for mail steps
        if has_mail_steps and not check_mailbox_exist(db, current_user):
            is_mailbox_warning = True
        if (
            not has_mail_steps
            and not has_linkedin_steps
            and not check_mailbox_exist(db, current_user)
        ):
            is_mailbox_warning = True
        if (
            not has_mail_steps
            and not has_linkedin_steps
            and not check_linkedin_sender_exist(db, current_user)
        ):
            is_linkedin_warning = True
        # Check LinkedIn account requirement for LinkedIn steps
        if has_linkedin_steps and not check_linkedin_sender_exist(db, current_user):
            is_linkedin_warning = True

    return UpdateCampaignResponse(
        is_credit_warning=is_credit_warning,
        is_mailbox_warning=is_mailbox_warning,
        is_linkedin_warning=is_linkedin_warning,
    )


def update_campaign_step_service(
    db: Session,
    current_user: UserBase,
    step_id: int,
    request: UpdateStepRequest,
):
    step, template = db.exec(
        select(SequenceCampaignStep, SequenceStepContentTemplate)
        .join(
            SequenceStepContentTemplate,
            SequenceCampaignStep.content_template_id == SequenceStepContentTemplate.id,
            isouter=True,
        )
        .where(
            SequenceCampaignStep.id == step_id,
            SequenceCampaignStep.deleted_at.is_(None),
        )
    ).first()
    if not step:
        raise NotFoundException("Step not found")
    # update updated_at in sequence
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == step.sequence_campaign_id,
            SequenceCampaign.deleted_at.is_(None),
        )
    ).first()
    if not campaign:
        raise NotFoundException("SequenceCampaign not found")
    campaign.updated_at = datetime.now()

    if request.is_active is True and step.is_active is False:
        service_code_pair = {
            StepType.MAIL_AUTO: ServiceCode.EMAIL,
            StepType.MAIL_MANUAL: ServiceCode.EMAIL,
            StepType.LINKEDIN_AUTO_MESSAGE: ServiceCode.LINKEDIN_MSG,
            StepType.LINKEDIN_CONNECTION_REQUEST: ServiceCode.LINKEDIN_MSG,
            StepType.LINKEDIN_VIEW_PROFILE: ServiceCode.LINKEDIN_MSG,
        }
        for step_type, service_code in service_code_pair.items():
            if step.step_type == step_type and not is_enough_credit(
                db, current_user.team_id, 1, service_code
            ):
                if service_code == ServiceCode.EMAIL:
                    raise BadRequestException(detail="sequence.notEnoughCreditEmail")
                else:
                    raise BadRequestException(
                        detail="sequence.notEnoughCreditLinkedinMsg"
                    )
        step.activated_at = datetime.now()
    if request.is_active is False:
        step.activated_at = None

    original_step_type = step.step_type

    step_type_pair = {
        StepType.MAIL_AUTO: StepType.MAIL_MANUAL,
        StepType.MAIL_MANUAL: StepType.MAIL_AUTO,
    }

    if request.step_type == StepType.LINKEDIN_VIEW_PROFILE:
        if request.step_type != original_step_type and template is not None:
            template.content = None
    else:
        step_type_to_content = {
            StepType.MAIL_AUTO: ContentType.MAIL,
            StepType.MAIL_MANUAL: ContentType.MAIL,
            StepType.LINKEDIN_AUTO_MESSAGE: ContentType.MESSAGE,
            StepType.LINKEDIN_CONNECTION_REQUEST: ContentType.NOTE,
        }
        content_type = step_type_to_content.get(request.step_type)

        if not content_type:
            return

        if request.step_type == StepType.LINKEDIN_AUTO_MESSAGE:
            step.is_active = False

        should_create_template = False
        if request.step_type != original_step_type:
            for current_step, incoming_step in step_type_pair.items():
                if (
                    original_step_type == current_step
                    and request.step_type != incoming_step
                ):
                    should_create_template = True
                    break

            if original_step_type not in (StepType.MAIL_AUTO, StepType.MAIL_MANUAL):
                should_create_template = True

        if should_create_template:
            title = "テンプレートの件名" if content_type != ContentType.NOTE else None
            new_template = SequenceStepContentTemplate(
                title=title,
                created_by=current_user.id,
                updated_by=current_user.id,
                content_type=content_type,
            )
            db.add(new_template)
            db.flush()
            db.refresh(new_template)
            step.content_template_id = new_template.id

    for attr, value in request.dict(exclude_unset=True).items():
        setattr(step, attr, value)

    if template is not None:
        db.add(template)
    if request.is_email_limit_enabled is False:
        step.email_limit_count = None
    if request.is_skip_enabled is False:
        step.skip_after_days = None
    step.updated_by = current_user.id
    step.updated_at = datetime.now()
    db.add(campaign)
    db.add(step)
    db.flush()
    db.refresh(step)

    # Recalculate total_days for all steps in this campaign after updates
    steps_in_campaign = db.exec(
        select(SequenceCampaignStep)
        .where(
            SequenceCampaignStep.sequence_campaign_id == step.sequence_campaign_id,
            SequenceCampaignStep.deleted_at.is_(None),
        )
        .order_by(SequenceCampaignStep.order.asc())
    ).all()
    if steps_in_campaign:
        for index, s in enumerate(steps_in_campaign, start=1):
            s.total_days = get_total_days_count(steps_in_campaign[:index])
            db.add(s)

    db.commit()
    return step.id


def delete_campaign_service(
    db: Session, current_user: UserBase, campaign_ids: List[int]
):
    campaigns = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id.in_(campaign_ids),
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).all()
    if not campaigns:
        raise NotFoundException("Campaign not found")
    try:
        for campaign in campaigns:
            campaign.deleted_at = datetime.now()
            campaign.deleted_by = current_user.id
        db.commit()
    except Exception as e:
        print(e)
        db.rollback()
        return False
    return True


def delete_step_service(db: Session, current_user: UserBase, step_id: int):
    step = db.exec(
        select(SequenceCampaignStep).where(
            SequenceCampaignStep.id == step_id,
            SequenceCampaignStep.deleted_at.is_(None),
        )
    ).first()
    if not step:
        raise NotFoundException("Step not found")
    # update sequence.updated_at
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == step.sequence_campaign_id,
            SequenceCampaign.deleted_at.is_(None),
        )
    ).first()
    if not campaign:
        raise NotFoundException("SequenceCampaign not found")
    campaign.updated_at = datetime.now()
    db.add(campaign)
    try:
        step.deleted_at = datetime.now()
        step.deleted_by = current_user.id
        db.add(step)
        db.flush()
        db.refresh(step)

        next_steps = db.exec(
            select(SequenceCampaignStep)
            .where(
                SequenceCampaignStep.sequence_campaign_id == step.sequence_campaign_id,
                SequenceCampaignStep.deleted_at.is_(None),
            )
            .order_by(SequenceCampaignStep.order.asc())
        ).all()
        if next_steps:
            for next_step in next_steps:
                if next_step.order > step.order:
                    next_step.order = next_step.order - 1
                    next_step.total_days = get_total_days_count(
                        next_steps[: next_step.order]
                    )
                    db.add(next_step)
            db.flush()
        update_mail_history_next_step(db, step)
        db.execute(
            update(SequenceTask)
            .where(SequenceTask.sequence_step_id == step_id)
            .values(
                deleted_at=datetime.now(),
                deleted_by=current_user.id,
            )
        )
        db.exec(
            update(SequenceMailHistory)
            .where(
                SequenceMailHistory.sequence_step_id == step_id,
                SequenceMailHistory.status.in_(
                    [MailHistoryStatus.SCHEDULED, MailHistoryStatus.FAILED]
                ),
            )
            .values(
                deleted_at=datetime.now(),
                deleted_by=current_user.id,
            )
        )
        db.flush()
        all_contact_ids = set(
            db.exec(
                select(SequenceContact.id).where(
                    SequenceContact.deleted_at.is_(None),
                    SequenceContact.sequence_campaign_id == campaign.id,
                )
            ).all()
        )

        not_finish_contact_ids = set(
            db.exec(
                select(SequenceContact.id)
                .join(
                    SequenceCampaignContacts,
                    SequenceContact.id == SequenceCampaignContacts.sequence_contact_id,
                )
                .join(
                    SequenceCampaign,
                    SequenceCampaign.id
                    == SequenceCampaignContacts.sequence_campaign_id,
                )
                .join(
                    SequenceCampaignStep,
                    SequenceCampaignStep.sequence_campaign_id == SequenceCampaign.id,
                )
                .where(
                    SequenceCampaign.id == campaign.id,
                    SequenceContact.deleted_at.is_(None),
                    SequenceCampaignStep.deleted_at.is_(None),
                    SequenceCampaignContacts.status == StatusEnum.ACTIVE,
                    SequenceContact.current_step == SequenceCampaignStep.order,
                )
            ).all()
        )

        finish_contact_ids = all_contact_ids - not_finish_contact_ids

        if finish_contact_ids:
            db.exec(
                update(SequenceCampaignContacts)
                .where(
                    SequenceCampaignContacts.sequence_contact_id.in_(
                        finish_contact_ids
                    ),
                    SequenceCampaignContacts.status.in_(
                        [StatusEnum.ACTIVE, StatusEnum.NOT_SENT]
                    ),
                )
                .values(status=StatusEnum.FINISH, updated_at=datetime.now())
            )
        db.commit()
    except Exception as e:
        print(e)
        db.rollback()
        return False
    return True


def update_mail_history_next_step(db: Session, current_step: SequenceCampaignStep):
    next_step = db.exec(
        select(SequenceCampaignStep)
        .where(
            SequenceCampaignStep.sequence_campaign_id
            == current_step.sequence_campaign_id,
            SequenceCampaignStep.order == current_step.order,
            SequenceCampaignStep.deleted_at.is_(None),
        )
        .order_by(SequenceCampaignStep.order.asc())
    ).first()

    next_step_id = next_step.id if next_step else None

    db.exec(
        update(SequenceMailHistory)
        .where(
            SequenceMailHistory.next_sequence_step_id == current_step.id,
            SequenceMailHistory.deleted_at.is_(None),
        )
        .values(next_sequence_step_id=next_step_id)
    )
