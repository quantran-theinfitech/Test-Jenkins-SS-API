# flake8: noqa: E501

from sqlmodel import Session, and_, case, func, select, text

from app.api.v1.schemas.sequence.mail_histories import (
    ListingMailHistoryRequest,
    MailHistoryBase,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.media import media_service
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.contact import SequenceContact
from app.models.sequence.email_schedule import SequenceEmailSchedule
from app.models.sequence.mail_alias import SequenceMailAlias

# from app.models.sequence.mail_alias_setting import (
#     SequenceMailAliasSetting,
#     SettingOption,
# )
from app.models.sequence.mail_history import (
    MAIL_HISTORY_VIEW_NAME,
    MailHistoryBounceSubType,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.user import User
from utils.mailbox_utils import get_mail_alias_setting


def listing_mail_histories_with_view_service(
    db: Session,
    sequence_campaign_id: int,
    request: ListingMailHistoryRequest,
    current_user: UserBase,
    # mails: Optional[List[str]] = None,
    # alias_emails: Optional[List[str]] = None,
    # mail_senders: Optional[List[str]] = None
):
    condition = ""
    params = {
        "sequence_campaign_id": sequence_campaign_id,
        "exclude_status": MailHistoryStatus.SKIPPED.value,
    }
    if request.status:
        condition += " AND v.status = :status"
        params["status"] = request.status

    # if len(mails) or len(alias_emails):
    # mail_alias_settings = db.exec(
    #     select(SequenceMailAliasSetting).where(
    #         SequenceMailAliasSetting.sequence_campaign_id == sequence_campaign_id,
    #         or_(
    #             SequenceMailAliasSetting.mailbox_id.in_(mails),
    #             SequenceMailAliasSetting.mailbox_alias_id.in_(alias_emails),
    #         ),
    #     )
    # ).all()
    # mailboxes = db.exec(
    #     select(SequenceMailbox).where(SequenceMailbox.id.in_(mails))
    # ).all()
    # aliases = db.exec(
    #     select(SequenceMailAlias).where(SequenceMailAlias.id.in_(alias_emails))
    # ).all()
    # contact_alias_list = []
    # step_alias_list = []
    # email_from_list = [mailbox.email for mailbox in mailboxes]
    # email_from_list.extend([alias.alias_email for alias in aliases])
    # for setting in mail_alias_settings:
    #     if setting.setting_option == SettingOption.CONTACT:
    #         contact_alias_list.append(setting.sequence_person_id)
    #     if setting.setting_option == SettingOption.STEP:
    #         step_alias_list.append(
    #             (setting.sequence_person_id, setting.sequence_step_id)
    #         )
    # alias_condition = "0 = 1"  # Always false condition
    # alias_condition += " OR v.mailbox_alias_id = ANY (:alias_emails)"
    # params["alias_emails"] = alias_emails
    # alias_condition += (
    #     " OR (v.sequence_mailbox_id = ANY (:mails) AND v.mailbox_alias_id IS NULL)"
    # )
    # params["mails"] = mails
    # if len(contact_alias_list):
    #     alias_condition += " OR v.sequence_person_id = ANY (:contact_alias_list)"
    #     params["contact_alias_list"] = contact_alias_list
    # if len(step_alias_list):
    #     alias_condition += " OR (v.sequence_person_id, v.sequence_step_id) = ANY (:step_alias_list)"
    #     params["step_alias_list"] = step_alias_list
    # if len(email_from_list):
    #     alias_condition += " OR v.mailbox_alias_id = ANY (:email_from_list)"
    #     params["email_from_list"] = email_from_list
    # condition += f" AND ({alias_condition})"

    if request.mail_senders:
        condition += " AND v.email_from = ANY (:mail_senders)"
        params["mail_senders"] = request.mail_senders
    if request.step_ids and len(request.step_ids) > 0:
        condition += " AND v.sequence_step_id = ANY (:step_ids)"
        params["step_ids"] = request.step_ids
    if request.contact_ids and len(request.contact_ids) > 0:
        condition += " AND v.sequence_contact_id = ANY (:contact_ids)"
        params["contact_ids"] = request.contact_ids
    if request.keyword:
        condition += (
            " AND (v.title ILIKE :keyword OR v.sequence_person_name ILIKE :keyword)"
        )
        params["keyword"] = f"%{request.keyword}%"

    result = (
        db.exec(
            text(
                f"""SELECT v.*, smt.*, scs.step_type, v.title AS mail_history_title, v.content AS mail_history_content
        FROM {MAIL_HISTORY_VIEW_NAME} v
        JOIN sequence_campaign_steps scs ON scs.id = v.sequence_step_id
        JOIN sequence_step_content_templates smt ON scs.content_template_id = smt.id
        WHERE
            v.sequence_campaign_id = :sequence_campaign_id
            AND v.to_address IS NOT NULL
            AND v.status != :exclude_status
            AND (scs.step_type = 'MAIL_AUTO' OR scs.step_type = 'MAIL_MANUAL')
            {condition}
        ORDER BY CASE v.status
                WHEN '{MailHistoryStatus.SCHEDULED}' THEN 1
                ELSE 2
            END, v.sent_at DESC
        LIMIT {request.per_page}
        OFFSET {(request.page - 1) * request.per_page}
        """
            ),
            params=params,
        )
        .mappings()
        .all()
    )

    response = []
    for mail_history in result:
        print(f"mail_history: {mail_history.sent_at}")
        mail_history_res = MailHistoryBase(**dict(mail_history))
        mail_history_res.title = mail_history["mail_history_title"]
        mail_history_res.content = mail_history["mail_history_content"]

        # if mail_history.sequence_mailbox_id:
        #     mailbox = db.exec(
        #         select(SequenceMailbox).where(
        #             SequenceMailbox.id == mail_history.sequence_mailbox_id,
        #             SequenceMailbox.deleted_at.is_(None),
        #         )
        #     ).first()

        #     mail_history_res.mailbox = mailbox
        # result = get_mail_alias_setting(
        #     db,
        #     mail_history.sequence_campaign_id,
        #     mail_history.sequence_step_id,
        #     mail_history.sequence_contact_id,
        # )
        # if result:
        #     alias_mailbox, mail_alias = result
        #     if alias_mailbox:
        #         mail_history_res.mailbox = alias_mailbox
        #         mail_history_res.sequence_mailbox_id = alias_mailbox.id
        #     if mail_alias:
        #         mail_history_res.sequence_mailbox_alias_id = mail_alias.id
        #         mail_history_res.email_from = mail_alias.alias_email
        #         mail_history_res.sender_name = mail_alias.alias_name
        user = db.get(User, mail_history_res.sent_by)
        mail_history_res.sender_avatar = (
            media_service.get_presigned_url(user.avatar_path)
            if user and user.avatar_path
            else None
        )
        # if mail_history.status == MailHistoryStatus.SCHEDULED and mail_history.scheduled_at:
        response.append(mail_history_res)

    total_result = (
        db.exec(
            text(
                f"""SELECT COUNT(*) AS total
        FROM {MAIL_HISTORY_VIEW_NAME} v
        WHERE
            v.sequence_campaign_id = :sequence_campaign_id
            AND v.status != :exclude_status
            AND v.to_address IS NOT NULL
            {condition}
        """
            ),
            params=params,
        )
        .mappings()
        .first()
    )
    total = 0
    if total_result:
        total = total_result["total"]
    return response, total


def get_mail_history_statistics_with_view_service(
    db: Session,
    sequence_campaign_id: int,
    current_user: UserBase,
):
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    spam_subtype = [
        MailHistoryBounceSubType.SUPPRESSED.value,
        MailHistoryBounceSubType.ON_ACCOUNT_SUPPRESSION_LIST.value,
        MailHistoryBounceSubType.CONTENT_REJECTED.value,
        MailHistoryBounceSubType.ATTACHMENT_REJECTED.value,
    ]
    params = {
        # "spam_subtype": spam_subtype,
        "sequence_campaign_id": sequence_campaign_id,
        "exclude_status": MailHistoryStatus.SKIPPED.value,
    }
    result = (
        db.exec(
            text(
                f"""SELECT count(*) AS total,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.SENT.value}'
                        OR v.status = '{MailHistoryStatus.OPENED.value}'
                        OR v.status = '{MailHistoryStatus.REPLIED.value}'
                        OR v.status = '{MailHistoryStatus.BOUNCED.value}'
                        OR v.status = '{MailHistoryStatus.OPT_OUT.value}'
                    ) THEN 1
                END) AS delivered_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.SCHEDULED.value}'
                    ) THEN 1
                END) AS scheduled_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.OPENED.value}'
                    ) THEN 1
                END) AS opened_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.DRAFT.value}'
                    ) THEN 1
                END) AS draft_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.NOT_SENT.value}'
                    ) THEN 1
                END) AS not_sent_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.FAILED.value}'
                    ) THEN 1
                END) AS failed_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.REPLIED.value}'
                    ) THEN 1
                END) AS replied_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.BOUNCED.value}'
                        AND smh.bounce_sub_type IN {tuple(spam_subtype)}
                    ) THEN 1
                END) AS spam_blocked_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.BOUNCED.value}'
                        AND smh.bounce_sub_type NOT IN {tuple(spam_subtype)}
                    ) THEN 1
                END) AS bounced_count,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.OPT_OUT.value}'
                    ) THEN 1
                END) AS unsubscribed_count
        FROM {MAIL_HISTORY_VIEW_NAME} v
        JOIN sequence_campaign_steps scs ON v.sequence_step_id = scs.id
        LEFT JOIN sequence_mail_histories smh ON v.mail_history_id = smh.id
        WHERE
            v.sequence_campaign_id = :sequence_campaign_id
            AND v.status != :exclude_status
            AND (scs.step_type = 'MAIL_AUTO' OR scs.step_type = 'MAIL_MANUAL')
            AND v.to_address IS NOT NULL
        """
            ),
            params=params,
        )
        .mappings()
        .first()
    )
    result = dict(result)
    return result


def listing_mail_histories_service(
    db: Session,
    sequence_campaign_id: int,
    request: ListingMailHistoryRequest,
    current_user: UserBase,
):
    query = (
        select(
            SequenceMailHistory,
            SequenceCampaign,
            SequenceCampaignStep,
            SequenceContact,
            SequenceEmailSchedule,
            SequenceMailbox,
        )
        .join(
            SequenceMailbox,
            SequenceMailbox.id == SequenceMailHistory.sequence_mailbox_id,
            isouter=True,
        )
        .join(
            SequenceCampaign,
            SequenceCampaign.id == SequenceMailHistory.sequence_campaign_id,
            isouter=True,
        )
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
            isouter=True,
        )
        .join(
            SequenceContact,
            SequenceContact.id == SequenceMailHistory.sequence_contact_id,
            isouter=True,
        )
        .join(
            SequenceEmailSchedule,
            SequenceEmailSchedule.mail_history_id == SequenceMailHistory.id,
            isouter=True,
        )
        .where(
            SequenceMailHistory.sequence_campaign_id == sequence_campaign_id,
            SequenceMailHistory.deleted_at.is_(None),
            SequenceMailbox.deleted_at.is_(None),
        )
    )
    if request.status:
        query = query.where(SequenceMailHistory.status == request.status)
    if request.mailbox_ids and len(request.mailbox_ids) > 0:
        query = query.where(
            SequenceMailHistory.sequence_mailbox_id.in_(request.mailbox_ids),
        )
    if request.step_ids and len(request.step_ids) > 0:
        query = query.where(
            SequenceMailHistory.sequence_step_id.in_(request.step_ids),
        )
    mail_histories = db.exec(
        query.offset((request.page - 1) * request.per_page)
        .limit(request.per_page)
        .order_by(SequenceMailHistory.id.desc())
    ).all()
    mail_histories_response = []

    for (
        mail_history,
        sequence_campaign_name,
        sequence_step_order,
        sequence_person_name,
        sequence_email_schedule,
        mailbox,
    ) in mail_histories:
        item = MailHistoryBase(
            **mail_history.dict(),
            sender_name=current_user.name,
            sequence_person_name=(
                sequence_person_name.name if sequence_person_name else None
            ),
            sequence_campaign_name=(
                sequence_campaign_name.name if sequence_campaign_name else None
            ),
            sequence_step_order=(
                sequence_step_order.order if sequence_step_order else None
            ),
            email_from=mailbox.email if mailbox else None,
            mailbox=mailbox if mailbox else None,
        )
        if (
            mail_history.status == MailHistoryStatus.SCHEDULED
            and sequence_email_schedule
        ):
            item.sent_at = sequence_email_schedule.scheduled_at
        mail_histories_response.append(item)
    total_query = query.with_only_columns(func.count()).order_by(None)

    total = db.exec(total_query).scalar()

    return mail_histories_response, total


def get_mail_history_statistics_service(
    db: Session,
    sequence_campaign_id: int,
):
    query = select(
        func.count(SequenceMailHistory.id).label("total"),
        func.count(
            case(
                (
                    and_(
                        SequenceMailHistory.status == MailHistoryStatus.SENT,
                    ),
                    1,
                ),
                else_=None,
            )
        ).label("delivered_count"),
        func.count(
            case(
                (
                    and_(
                        SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
                    ),
                    1,
                ),
                else_=None,
            )
        ).label("scheduled_count"),
        func.count(
            case(
                (
                    and_(
                        SequenceMailHistory.status == MailHistoryStatus.OPENED,
                    ),
                    1,
                ),
                else_=None,
            )
        ).label("opened_count"),
        func.count(
            case(
                (
                    and_(
                        SequenceMailHistory.status == MailHistoryStatus.DRAFT,
                    ),
                    1,
                ),
                else_=None,
            )
        ).label("draft_count"),
        func.count(
            case(
                (
                    and_(
                        SequenceMailHistory.status == MailHistoryStatus.FAILED,
                    ),
                    1,
                ),
                else_=None,
            )
        ).label("not_sent_count"),
        func.count(
            case(
                (
                    and_(
                        SequenceMailHistory.status == MailHistoryStatus.REPLIED,
                    ),
                    1,
                ),
                else_=None,
            )
        ).label("replied_count"),
    ).where(
        SequenceMailHistory.sequence_campaign_id == sequence_campaign_id,
        SequenceMailHistory.deleted_at.is_(None),
        SequenceMailHistory.status != MailHistoryStatus.SKIPPED,
    )

    (
        total,
        delivered_count,
        scheduled_count,
        opened_count,
        draft_count,
        not_sent_count,
        replied_count,
    ) = db.exec(query).first()
    return {
        "total": total,
        "delivered_count": delivered_count,
        "scheduled_count": scheduled_count,
        "opened_count": opened_count,
        "draft_count": draft_count,
        "not_sent_count": not_sent_count,
        "replied_count": replied_count,
    }
