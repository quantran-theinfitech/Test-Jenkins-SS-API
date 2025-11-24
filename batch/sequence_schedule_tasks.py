# flake8: noqa: E501
from datetime import datetime, timedelta, timezone

from celery import chain
from redis import Redis
from sqlmodel import (
    Date,
    Session,
    case,
    cast,
    extract,
    func,
    select,
    text,
    tuple_,
    update,
)

from app.db import engine
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.campaign_setting import SequenceCampaignSetting
from app.models.sequence.contact import SequenceContact
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.mail_history import (
    MAIL_HISTORY_VIEW_NAME,
    AccountOption,
    FailCode,
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.redis import redis_host, redis_port
from celery_worker import trigger_linkedin, trigger_mail
from external.mail_tracking import MailTrackingService
from utils.mailbox_utils import get_mail_alias_setting
from utils.sequence_schedule import validate_campaign_on_sending_window


# python -m batch.main handle_sequence_schedule_task --interval_minutes=30
def handle_sequence_schedule_tasks(args):
    BATCH_SIZE = 500
    db = Session(engine)

    redis_client = Redis(host=redis_host, port=int(redis_port), ssl=False)

    query_base = f"""
        FROM {MAIL_HISTORY_VIEW_NAME} v
        JOIN sequence_campaigns sc ON v.sequence_campaign_id = sc.id
        WHERE
            v.status = :status
            AND sc.is_active IS TRUE
            AND v.process_status IS NULL
        """

    # Dùng while loop thay vì for range vì danh sách thay đổi sau mỗi lần commit (records drop out of the WHERE clause)
    while True:
        query_select = (
            "SELECT v.*"
            + query_base
            + f" ORDER BY v.sequence_step_order ASC, v.sent_at ASC LIMIT {BATCH_SIZE}"
        )

        tasks = [
            dict(row)
            for row in (
                db.exec(
                    text(query_select),
                    params={
                        "status": MailHistoryStatus.SCHEDULED,
                        # "schedule_date": datetime.now(timezone.utc),
                    },
                )
                .mappings()
                .all()
            )
        ]

        if not tasks:
            print("No more tasks to process")
            break

        print(f"Processing batch of {len(tasks)} tasks")
        campaign_ids = list(
            {
                task["sequence_campaign_id"]
                for task in tasks
                if task["sequence_campaign_id"]
            }
        )
        if campaign_ids:
            service = MailTrackingService()
            service.replied_tracking(db, timedelta(weeks=2), campaign_ids)
        all_contact_ids = [task["sequence_contact_id"] for task in tasks]
        # last_sent_times = db.exec(
        #     select(
        #         SequenceMailHistory.sequence_contact_id,
        #         func.max(SequenceMailHistory.sent_at),
        #     )
        #     .where(
        #         SequenceMailHistory.sequence_contact_id.in_(all_contact_ids),
        #         SequenceMailHistory.status.not_in(
        #             [
        #                 MailHistoryStatus.SKIPPED,
        #                 MailHistoryStatus.SCHEDULED,
        #                 MailHistoryStatus.FAILED,
        #             ]
        #         ),
        #         SequenceMailHistory.sent_at <= datetime.now(timezone.utc),
        #     )
        #     .group_by(SequenceMailHistory.sequence_contact_id)
        # ).all()

        # # Chuyển kết quả thành dict: {person_id: last_sent_at}
        # last_sent_time_per_contact = {
        #     person_id: (
        #         sent_at.replace(tzinfo=timezone.utc)
        #         if sent_at is not None
        #         and (sent_at.tzinfo is None or sent_at.tzinfo.utcoffset(sent_at) is None)
        #         else (sent_at.astimezone(timezone.utc) if sent_at is not None else None)
        #     )
        #     for person_id, sent_at in last_sent_times
        # }

        query = (
            select(
                SequenceContact,
                SequenceCampaignSetting,
            )
            .join(
                SequenceCampaignSetting,
                SequenceCampaignSetting.sequence_campaign_id
                == SequenceContact.sequence_campaign_id,
            )
            .where(SequenceContact.id.in_(all_contact_ids))
        )
        result = db.exec(query).all()
        contact_block_list = {}
        contact_not_sent_list = []
        for contact, setting in result:
            if contact.stage in setting.stage_list_as_not_sent:
                contact_block_list[contact.id] = True
                contact_not_sent_list.append((contact.id, setting.sequence_campaign_id))

        mailbox_limit = {}
        mailbox_tasks = {}
        linkedin_account_limit = {}
        linkedin_account_tasks = {}
        mail_history_list = {}

        for task in tasks:
            mail_history_id = task["mail_history_id"]
            mail_history = None
            if mail_history_id:
                mail_history = db.exec(
                    select(SequenceMailHistory).where(
                        SequenceMailHistory.id == mail_history_id
                    )
                ).first()
            if not mail_history:
                mail_history = SequenceMailHistory(**task)
                db.add(mail_history)
                db.flush()
                task["mail_history_id"] = mail_history.id
            mail_history_list[mail_history.id] = mail_history
            mail_history.process_status = MailHistoryProcessStatus.PENDING
        db.commit()
        for mail_history in mail_history_list.values():
            db.refresh(mail_history)
        print(f"Total mail histories to process: {len(mail_history_list)}")
        for task in tasks:
            mail_history = mail_history_list.get(task["mail_history_id"], None)
            if not mail_history:
                print(f"No mail history found for task {task}")
                continue
            mail_history_id = mail_history.id
            if mail_history.is_rescheduled is True:
                sent_at = mail_history.sent_at
                if sent_at is not None and sent_at.replace(
                    tzinfo=timezone.utc
                ) > datetime.now(timezone.utc):
                    mail_history.process_status = None
                    continue
            elif mail_history.is_rescheduled is not True:
                try:
                    is_valid, schedule = validate_campaign_on_sending_window(
                        db, mail_history.sequence_campaign_id
                    )
                    if not is_valid:
                        print(f"Mail history {mail_history_id} not in sending window")
                        if not schedule:
                            print(
                                f"""Mail history {mail_history_id}
                                not found next sending window"""
                            )
                            mail_history.status = MailHistoryStatus.FAILED
                            mail_history.fail_reason = "Not in next sending window"
                            mail_history.process_status = None
                            continue
                        mail_history.sent_at = schedule
                        mail_history.process_status = None
                        continue
                except Exception as e:
                    print(
                        f"""Error when validate sending window for mail history
                        {mail_history_id} with error {str(e)}"""
                    )
                    mail_history.process_status = None
                    continue
            campaign = db.exec(
                select(SequenceCampaign).where(
                    SequenceCampaign.id == mail_history.sequence_campaign_id
                )
            ).first()

            task_step = db.exec(
                select(SequenceCampaignStep).where(
                    SequenceCampaignStep.id == mail_history.sequence_step_id,
                    SequenceCampaignStep.deleted_at.is_(None),
                )
            ).first()
            if not task_step:
                print(
                    f"Sequence step not found for mail history {mail_history_id}, skipping"
                )
                mail_history.status = MailHistoryStatus.FAILED
                mail_history.fail_reason = "Sequence step not found"
                continue
            if (
                task_step.step_type == StepType.MAIL_AUTO
                or task_step.step_type == StepType.MAIL_MANUAL
            ):
                handel_mail_tasks(
                    db,
                    mail_history_id,
                    mail_history,
                    campaign,
                    mailbox_limit,
                    mailbox_tasks,
                    task,
                )

            elif (
                task_step.step_type == StepType.LINKEDIN_VIEW_PROFILE
                or task_step.step_type == StepType.LINKEDIN_CONNECTION_REQUEST
                or task_step.step_type == StepType.LINKEDIN_AUTO_MESSAGE
            ):
                handel_linkedin_tasks(
                    db,
                    mail_history_id,
                    mail_history,
                    campaign,
                    linkedin_account_limit,
                    linkedin_account_tasks,
                    task,
                    task_step.step_type,
                )
        handle_trigger_mail_tasks(
            db,
            mailbox_limit,
            mailbox_tasks,
            contact_block_list,
            contact_not_sent_list,
        )

        handle_trigger_linkedin_tasks(
            db,
            linkedin_account_limit,
            linkedin_account_tasks,
            contact_block_list,
            contact_not_sent_list,
            redis_client,
        )

        db.commit()
        db.expire_all()
        del mail_history_list
        del mailbox_tasks
        del linkedin_account_tasks


def handel_mail_tasks(
    db: Session,
    mail_history_id: int,
    mail_history: SequenceMailHistory,
    campaign: SequenceCampaign,
    mailbox_limit: dict,
    mailbox_tasks: dict,
    task: dict,
):
    mailbox = None
    if not mail_history.sequence_mailbox_id:
        mailbox = db.exec(
            select(SequenceMailbox)
            .where(
                SequenceMailbox.created_by == campaign.created_by,
                SequenceMailbox.deleted_at.is_(None),
            )
            .order_by(SequenceMailbox.id.asc())
        ).first()
        if mailbox:
            mail_history.sequence_mailbox_id = mailbox.id
    else:
        mailbox = db.get(SequenceMailbox, mail_history.sequence_mailbox_id)

    result = get_mail_alias_setting(
        db,
        mail_history.sequence_campaign_id,
        mail_history.sequence_step_id,
        mail_history.sequence_contact_id,
    )
    if result:
        alias_mailbox = result[0]
        if alias_mailbox:
            mailbox = alias_mailbox

    if not mailbox:
        print(
            f"""
            Mail history {mail_history_id} has no mailbox, skipping task scheduling.
            """
        )
        db.exec(
            update(SequenceCampaignContacts)
            .where(
                SequenceCampaignContacts.sequence_contact_id
                == mail_history.sequence_contact_id,
                SequenceCampaignContacts.sequence_campaign_id
                == mail_history.sequence_campaign_id,
            )
            .values(status=StatusEnum.NOT_SENT.value)
        )
        mail_history.status = MailHistoryStatus.NOT_SENT
        mail_history.fail_reason = FailCode.EMAIL_NOT_FOUND
        mail_history.sent_at = datetime.now()
        return

    if not mailbox_limit.get(mailbox.id):
        current_hour_sent, current_day_sent = db.exec(
            select(
                func.count(
                    case(
                        (
                            extract("hour", SequenceMailHistory.sent_at)
                            == extract("hour", func.now()),
                            1,
                        ),
                        else_=None,
                    )
                ).label("current_hour_sent"),
                func.count().label("current_day_sent"),
            ).where(
                SequenceMailHistory.sequence_mailbox_id == mailbox.id,
                cast(SequenceMailHistory.sent_at, Date) == cast(func.now(), Date),
                SequenceMailHistory.status.not_in(
                    [
                        MailHistoryStatus.SKIPPED,
                        MailHistoryStatus.SCHEDULED,
                        MailHistoryStatus.FAILED,
                    ]
                ),
            )
        ).first()
        mailbox_limit[mailbox.id] = {
            "current_hour_sent": current_hour_sent,
            "current_day_sent": current_day_sent,
            "emails_sent_per_hour": mailbox.emails_sent_per_hour,
            "emails_sent_per_day": mailbox.emails_sent_per_day,
        }
    if not mailbox_tasks.get(mailbox.id):
        mailbox_tasks[mailbox.id] = []
    mailbox_tasks[mailbox.id].append(
        {
            "mail_history": mail_history,
            "id": mail_history_id,
            "sent_at": (
                task["sent_at"].replace(tzinfo=timezone.utc)
                if task["sent_at"] is not None
                and (
                    task["sent_at"].tzinfo is None
                    or task["sent_at"].tzinfo.utcoffset(task["sent_at"]) is None
                )
                else (
                    task["sent_at"].astimezone(timezone.utc)
                    if task["sent_at"] is not None
                    else None
                )
            ),
        }
    )


def handel_linkedin_tasks(
    db: Session,
    mail_history_id: int,
    mail_history: SequenceMailHistory,
    campaign: SequenceCampaign,
    linkedin_account_limit: dict,
    linkedin_account_tasks: dict,
    task: dict,
    step_type: StepType,
):
    linkedin_account = None
    if (
        not mail_history.sequence_linkedin_account_id
        or mail_history.account_option is None
    ):
        linkedin_account = db.exec(
            select(LinkedInAccount)
            .where(
                LinkedInAccount.user_id == campaign.created_by,
                LinkedInAccount.deleted_at.is_(None),
            )
            .order_by(LinkedInAccount.id.asc())
        ).first()
        if not linkedin_account:
            linkedin_account = db.exec(
                select(LinkedInAccount)
                .where(
                    LinkedInAccount.team_id == campaign.team_id,
                    LinkedInAccount.deleted_at.is_(None),
                )
                .order_by(LinkedInAccount.id.asc())
            ).first()
        if linkedin_account:
            mail_history.sequence_linkedin_account_id = linkedin_account.id

    else:
        linkedin_account = db.get(
            LinkedInAccount, mail_history.sequence_linkedin_account_id
        )

    if not linkedin_account:
        print(
            f"Mail history {mail_history_id} has no linkedin account, skipping task scheduling."
        )
        db.exec(
            update(SequenceCampaignContacts)
            .where(
                SequenceCampaignContacts.sequence_contact_id
                == mail_history.sequence_contact_id,
                SequenceCampaignContacts.sequence_campaign_id
                == mail_history.sequence_campaign_id,
            )
            .values(status=StatusEnum.NOT_SENT.value)
        )
        mail_history.status = MailHistoryStatus.NOT_SENT
        mail_history.fail_reason = FailCode.LINKEDIN_SENDER_NOT_FOUND
        mail_history.sent_at = datetime.now()
        return

    if not linkedin_account_limit.get(linkedin_account.id):
        current_day_sent = db.exec(
            select(func.count(SequenceMailHistory.id))
            .select_from(SequenceMailHistory)
            .join(
                SequenceCampaignStep,
                SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
            )
            .where(
                SequenceMailHistory.sequence_linkedin_account_id == linkedin_account.id,
                SequenceCampaignStep.step_type == StepType.LINKEDIN_AUTO_MESSAGE,
                cast(SequenceMailHistory.sent_at, Date) == cast(func.now(), Date),
                SequenceMailHistory.status.not_in(
                    [
                        MailHistoryStatus.SKIPPED,
                        MailHistoryStatus.SCHEDULED,
                        MailHistoryStatus.FAILED,
                    ],
                ),
            )
        ).first()

        current_week_sent = db.exec(
            select(func.count(SequenceMailHistory.id))
            .select_from(SequenceMailHistory)
            .join(
                SequenceCampaignStep,
                SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
            )
            .where(
                SequenceMailHistory.sequence_linkedin_account_id == linkedin_account.id,
                SequenceCampaignStep.step_type == StepType.LINKEDIN_AUTO_MESSAGE,
                SequenceMailHistory.sent_at >= func.date_trunc("week", func.now()),
                SequenceMailHistory.status.not_in(
                    [
                        MailHistoryStatus.SKIPPED,
                        MailHistoryStatus.SCHEDULED,
                        MailHistoryStatus.FAILED,
                    ],
                ),
            )
        ).first()

        pending_task_ids = db.exec(
            select(SequenceMailHistory.id).where(
                SequenceMailHistory.sequence_linkedin_account_id == linkedin_account.id,
                SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
                SequenceMailHistory.process_status == MailHistoryProcessStatus.PENDING,
            )
        ).all()

        current_day_view_profile_sent = db.exec(
            select(func.count(SequenceMailHistory.id))
            .select_from(SequenceMailHistory)
            .join(
                SequenceCampaignStep,
                SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
            )
            .where(
                SequenceMailHistory.sequence_linkedin_account_id == linkedin_account.id,
                SequenceCampaignStep.step_type == StepType.LINKEDIN_VIEW_PROFILE,
                cast(SequenceMailHistory.sent_at, Date) == cast(func.now(), Date),
                SequenceMailHistory.status.not_in(
                    [
                        MailHistoryStatus.SKIPPED,
                        MailHistoryStatus.SCHEDULED,
                        MailHistoryStatus.FAILED,
                    ],
                ),
            )
        ).first()
        current_day_connection_request_sent = db.exec(
            select(func.count(SequenceMailHistory.id))
            .select_from(SequenceMailHistory)
            .join(
                SequenceCampaignStep,
                SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
            )
            .where(
                SequenceMailHistory.sequence_linkedin_account_id == linkedin_account.id,
                SequenceCampaignStep.step_type == StepType.LINKEDIN_CONNECTION_REQUEST,
                cast(SequenceMailHistory.sent_at, Date) == cast(func.now(), Date),
                SequenceMailHistory.status.not_in(
                    [
                        MailHistoryStatus.SKIPPED,
                        MailHistoryStatus.SCHEDULED,
                        MailHistoryStatus.FAILED,
                    ],
                ),
            )
        ).first()

        current_week_connection_request_sent = db.exec(
            select(func.count(SequenceMailHistory.id))
            .select_from(SequenceMailHistory)
            .join(
                SequenceCampaignStep,
                SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
            )
            .where(
                SequenceMailHistory.sequence_linkedin_account_id == linkedin_account.id,
                SequenceCampaignStep.step_type == StepType.LINKEDIN_CONNECTION_REQUEST,
                SequenceMailHistory.sent_at >= func.date_trunc("week", func.now()),
                SequenceMailHistory.sent_at <= func.now(),
                SequenceMailHistory.status.not_in(
                    [
                        MailHistoryStatus.SKIPPED,
                        MailHistoryStatus.SCHEDULED,
                        MailHistoryStatus.FAILED,
                    ],
                ),
            )
        ).first()
        linkedin_account_limit[linkedin_account.id] = {
            "current_day_sent": current_day_sent,
            "current_week_sent": current_week_sent,
            "messages_sent_per_day": linkedin_account.messages_sent_per_day,
            "messages_sent_per_week": linkedin_account.messages_sent_per_week,
            "current_day_view_profile_sent": current_day_view_profile_sent,
            "profile_views_per_day": linkedin_account.profile_views_per_day,
            "current_day_connection_request_sent": current_day_connection_request_sent,
            "connections_sent_per_day": linkedin_account.connections_sent_per_day,
            "current_week_connection_request_sent": current_week_connection_request_sent,
            "connections_sent_per_week": linkedin_account.connections_sent_per_week,
            "request_interval_seconds": linkedin_account.request_interval_seconds,
            "pending_task_ids": pending_task_ids,
        }
    if not linkedin_account_tasks.get(linkedin_account.id):
        linkedin_account_tasks[linkedin_account.id] = []
    linkedin_account_tasks[linkedin_account.id].append(
        {
            "mail_history": mail_history,
            "id": mail_history_id,
            "sent_at": (
                task["sent_at"].replace(tzinfo=timezone.utc)
                if task["sent_at"] is not None
                and (
                    task["sent_at"].tzinfo is None
                    or task["sent_at"].tzinfo.utcoffset(task["sent_at"]) is None
                )
                else (
                    task["sent_at"].astimezone(timezone.utc)
                    if task["sent_at"] is not None
                    else None
                )
            ),
            "type": step_type,
        }
    )


def handle_trigger_mail_tasks(
    db: Session,
    mailbox_limit: dict,
    mailbox_tasks: dict,
    contact_block_list: dict,
    contact_not_sent_list: list,
):
    trigger_tasks = []
    current_date = datetime.now(timezone.utc)
    for mailbox_id, tasks in mailbox_tasks.items():
        current_hour_sent = mailbox_limit[mailbox_id]["current_hour_sent"]
        current_day_sent = mailbox_limit[mailbox_id]["current_day_sent"]
        emails_sent_per_hour = mailbox_limit[mailbox_id]["emails_sent_per_hour"]
        emails_sent_per_day = mailbox_limit[mailbox_id]["emails_sent_per_day"]
        for task in tasks:
            mail_history = task["mail_history"]
            # Normalize sent_at before any datetime comparison
            if task["sent_at"] is None:
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            if (
                task["sent_at"].tzinfo is None
                or task["sent_at"].tzinfo.utcoffset(task["sent_at"]) is None
            ):
                task["sent_at"] = task["sent_at"].replace(tzinfo=timezone.utc)
            if current_day_sent >= emails_sent_per_day:
                if current_date > task["sent_at"]:
                    schedule_tomorrow = (task["sent_at"] + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0
                    )
                    mail_history.sent_at = schedule_tomorrow
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            if current_hour_sent >= emails_sent_per_hour:
                if current_date > task["sent_at"]:
                    schedule_next_hour = (task["sent_at"] + timedelta(hours=1)).replace(
                        minute=0, second=0
                    )
                    mail_history.sent_at = schedule_next_hour
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            # Không kích hoạt trước thời điểm đã schedule
            if current_date < task["sent_at"]:
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            if contact_block_list.get(mail_history.sequence_contact_id, False):
                mail_history.status = MailHistoryStatus.FAILED
                mail_history.fail_reason = "Contact is blocked"
                continue
            current_hour_sent += 1
            current_day_sent += 1
            mail_history.process_status = MailHistoryProcessStatus.PENDING
            mail_history.status = MailHistoryStatus.SCHEDULED
            trigger_tasks.append(
                {
                    "id": task["id"],
                }
            )

    db.exec(
        update(SequenceCampaignContacts)
        .where(
            tuple_(
                SequenceCampaignContacts.sequence_contact_id,
                SequenceCampaignContacts.sequence_campaign_id,
            ).in_(contact_not_sent_list)
        )
        .values(
            status=StatusEnum.NOT_SENT.value,
            updated_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    for task in trigger_tasks:
        trigger_mail.apply_async((task["id"],))


def handle_trigger_linkedin_tasks(
    db: Session,
    linkedin_account_limit: dict,
    linkedin_account_tasks: dict,
    contact_block_list: dict,
    contact_not_sent_list: list,
    redis_client: Redis,
):

    trigger_tasks = {}
    current_date = datetime.now(timezone.utc)
    for linkedin_account_id, tasks in linkedin_account_tasks.items():
        current_day_sent = linkedin_account_limit[linkedin_account_id][
            "current_day_sent"
        ]
        current_week_sent = linkedin_account_limit[linkedin_account_id][
            "current_week_sent"
        ]
        messages_sent_per_day = linkedin_account_limit[linkedin_account_id][
            "messages_sent_per_day"
        ]
        messages_sent_per_week = linkedin_account_limit[linkedin_account_id][
            "messages_sent_per_week"
        ]
        current_day_view_profile_sent = linkedin_account_limit[linkedin_account_id][
            "current_day_view_profile_sent"
        ]
        profile_views_per_day = linkedin_account_limit[linkedin_account_id][
            "profile_views_per_day"
        ]
        current_day_connection_request_sent = linkedin_account_limit[
            linkedin_account_id
        ]["current_day_connection_request_sent"]
        connections_sent_per_day = linkedin_account_limit[linkedin_account_id][
            "connections_sent_per_day"
        ]
        current_week_connection_request_sent = linkedin_account_limit[
            linkedin_account_id
        ]["current_week_connection_request_sent"]
        connections_sent_per_week = linkedin_account_limit[linkedin_account_id][
            "connections_sent_per_week"
        ]

        step_limit_by_step_id = {}
        email_sent_count_by_step = {}
        step_is_email_limit_enabled_by_step_id = {}
        for task in tasks:
            mail_history = task["mail_history"]
            step_id = mail_history.sequence_step_id
            # Read per-step limit once per step id
            if step_id not in step_limit_by_step_id:
                step_limit_by_step_id[step_id] = db.exec(
                    select(SequenceCampaignStep.email_limit_count).where(
                        SequenceCampaignStep.id == step_id,
                        SequenceCampaignStep.is_email_limit_enabled == True,
                        extract("day", SequenceMailHistory.sent_at)
                        == extract("day", func.now()),
                    )
                ).first()
                step_is_email_limit_enabled_by_step_id[step_id] = db.exec(
                    select(SequenceCampaignStep.is_email_limit_enabled).where(
                        SequenceCampaignStep.id == step_id
                    )
                ).first()
            task_step_limit = step_limit_by_step_id.get(step_id)

            # Initialize already-sent count per step once per step id
            if step_id not in email_sent_count_by_step:
                email_sent_count_by_step[step_id] = db.exec(
                    select(func.count(SequenceMailHistory.id)).where(
                        SequenceMailHistory.sequence_step_id == step_id,
                        SequenceMailHistory.status.not_in(
                            [
                                MailHistoryStatus.SKIPPED,
                                MailHistoryStatus.SCHEDULED,
                                MailHistoryStatus.FAILED,
                            ],
                        ),
                    )
                ).first()

            # If limit is set and reached, reschedule
            if (
                task_step_limit is not None
                and email_sent_count_by_step[step_id] >= task_step_limit
                and step_is_email_limit_enabled_by_step_id[step_id] == True
            ):
                if current_date > task["sent_at"]:
                    schedule_tomorrow = (task["sent_at"] + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0
                    )
                    mail_history.sent_at = schedule_tomorrow
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            # Normalize sent_at before any datetime comparison
            if task["sent_at"] is None:
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            if (
                task["sent_at"].tzinfo is None
                or task["sent_at"].tzinfo.utcoffset(task["sent_at"]) is None
            ):
                task["sent_at"] = task["sent_at"].replace(tzinfo=timezone.utc)
            if (
                (
                    current_day_sent >= messages_sent_per_day
                    and task["type"] == StepType.LINKEDIN_AUTO_MESSAGE
                )
                or (
                    current_day_view_profile_sent >= profile_views_per_day
                    and task["type"] == StepType.LINKEDIN_VIEW_PROFILE
                )
                or (
                    current_day_connection_request_sent >= connections_sent_per_day
                    and task["type"] == StepType.LINKEDIN_CONNECTION_REQUEST
                )
            ):
                if current_date > task["sent_at"]:
                    schedule_tomorrow = (task["sent_at"] + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0
                    )
                    mail_history.sent_at = schedule_tomorrow
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            if (
                current_week_sent >= messages_sent_per_week
                and task["type"] == StepType.LINKEDIN_AUTO_MESSAGE
            ) or (
                current_week_connection_request_sent >= connections_sent_per_week
                and task["type"] == StepType.LINKEDIN_CONNECTION_REQUEST
            ):
                if current_date > task["sent_at"]:
                    schedule_next_week = (task["sent_at"] + timedelta(days=7)).replace(
                        hour=0, minute=0, second=0
                    )
                    mail_history.sent_at = schedule_next_week
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            # Không kích hoạt trước thời điểm đã schedule
            if current_date < task["sent_at"]:
                mail_history.process_status = None
                mail_history.status = MailHistoryStatus.SCHEDULED
                continue
            if contact_block_list.get(mail_history.sequence_contact_id, False):
                mail_history.status = MailHistoryStatus.FAILED
                mail_history.fail_reason = "Contact is blocked"
                continue
            current_day_sent += 1
            current_week_sent += 1
            current_day_view_profile_sent += 1
            current_day_connection_request_sent += 1
            current_week_connection_request_sent += 1
            step_id = mail_history.sequence_step_id
            if step_id in email_sent_count_by_step:
                email_sent_count_by_step[step_id] += 1
            else:
                email_sent_count_by_step[step_id] = 1
            mail_history.process_status = MailHistoryProcessStatus.PENDING
            mail_history.status = MailHistoryStatus.SCHEDULED
            if linkedin_account_id not in trigger_tasks:
                trigger_tasks[linkedin_account_id] = []
            trigger_tasks[linkedin_account_id].append(
                {
                    "id": task["id"],
                    "type": task["type"],
                }
            )
    db.exec(
        update(SequenceCampaignContacts)
        .where(
            tuple_(
                SequenceCampaignContacts.sequence_contact_id,
                SequenceCampaignContacts.sequence_campaign_id,
            ).in_(contact_not_sent_list)
        )
        .values(
            status=StatusEnum.NOT_SENT.value,
            updated_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    for linkedin_account_id, tasks in trigger_tasks.items():
        redis_prefix = f"lock:linkedin_account_id_{linkedin_account_id}"
        max_lock_time = 604800
        task_chain = []
        for i, task in enumerate(tasks):
            delay_seconds = (
                0
                if i == 0
                else linkedin_account_limit[linkedin_account_id][
                    "request_interval_seconds"
                ]
            )
            redis_key = f"{redis_prefix}:{task['id']}"
            redis_client.setex(redis_key, max_lock_time, "1")
            task_chain.append(
                trigger_linkedin.si(
                    task["id"],
                    task["type"],
                    linkedin_account_limit[linkedin_account_id]["pending_task_ids"],
                ).set(countdown=delay_seconds)
            )

        if task_chain:
            chain(*task_chain).apply_async()
