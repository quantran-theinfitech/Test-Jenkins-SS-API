import asyncio
import time
from email.header import Header
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import sentry_sdk
from celery import Celery, signals
from celery.schedules import crontab
from elasticsearch import AsyncElasticsearch
from fastapi_mail import ConnectionConfig
from pydantic import EmailStr
from redis import Redis
from sentry_sdk.integrations.celery import CeleryIntegration
from sqlmodel import Session, update

from app.config import settings
from app.db import engine
from app.es import es_basic_auth, es_url

from app.models.enrichment import Enrichment, EnrichmentStatus
from app.models.enrichment_file import EnrichmentFile
from app.models.sequence.campaign_import import UploadProcessStatus
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.mail_history import (
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.step import StepType
from app.redis import redis_host, redis_port
from celery_worker.cache_cross_search_first_steps_service import (
    cache_cross_search_first_steps_service,
)
from celery_worker.create_credit_service import create_credit_service
from celery_worker.hubspot_register_user_service import (
    upsert_user_from_hubspot_google_sheet,
)
from celery_worker.identify_enrichment_service import identify_enrichment_service
from celery_worker.resume_campaign_person_service import resume_campaign_person_service
from celery_worker.send_document_mail_to_new_user_service import (
    send_document_mail_to_new_user_service,
)
from celery_worker.send_jobs_to_sqs import send_jobs_to_sqs_service
from celery_worker.send_linhkedin_message_service import send_linkedin_message_service
from celery_worker.send_linkedin_connection_request_service import (
    send_linkedin_connection_request_service,
)
from celery_worker.sequence_person_tracking_service import tracking_unresponsive_person
from celery_worker.upload_enrichment_item_service import (
    upload_enrichment_item_from_file_service,
)
from celery_worker.upload_sequence_contact_service import save_to_db
from celery_worker.view_linkedin_profile_service import view_linkedin_profile_service

from .send_mail_service import handle_next_step, send_mail, skip_mail_service
from .track_mail_service import track_bounced_mail_service, track_replied_mail_service

celery = Celery(__name__)
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Configure task routes
# Tasks related to enrichment upload will be routed to a dedicated queue
# To run worker for enrichment queue with concurrency limit of 1:
# celery -A celery_worker worker -Q enrichment_upload -c 1 --loglevel=info
#
# To run worker for default queue:
# celery -A celery_worker worker -Q celery -c 4 --loglevel=info
# celery.conf.task_routes = {
#     "upload_enrichment_item_from_file": {
#         "queue": "enrichment_upload",
#         "priority": 1,  # Priority thấp (1-10, số càng cao càng ưu tiên)
#     },
#     "identify_enrichment": {
#         "queue": "enrichment_upload",
#         "priority": 1,  # Priority thấp
#     },
# }

# # Configure queue priorities
# celery.conf.task_default_priority = 7  # Tasks khác có priority cao hơn (7 > 1)

# # Configure queues with max priority
# # Cả 2 queue đều sử dụng x-max-priority=10 để hỗ trợ priority từ 1-10
# celery.conf.task_queues = [
#     Queue('celery', routing_key='celery', queue_arguments={'x-max-priority': 10}),
#     Queue('enrichment_upload', routing_key='enrichment_upload',
#          max_priority=10),
# ]


@signals.beat_init.connect
@signals.celeryd_init.connect
def init_sentry(**_kwargs):
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            # Add request headers and IP for users,
            # see
            # https://docs.sentry.io/platforms/python/data-management/data-collected/
            # for more info
            send_default_pii=True,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=1.0,
            # To collect profiles for all profile sessions,
            # set `profile_session_sample_rate` to 1.0.
            profile_session_sample_rate=1.0,
            # Profiles will be automatically collected while
            # there is an active span.
            profile_lifecycle="trace",
            integrations=[
                CeleryIntegration(
                    monitor_beat_tasks=True,
                    # add exclude task here
                    exclude_beat_tasks=[],
                ),
            ],
            environment=settings.SENTRY_ENV,
        )


@celery.task(name="trigger_mail")
def trigger_mail(mail_history_id: int):
    print(f"Start task for mail history {mail_history_id}")
    db = Session(engine)
    mail_history = asyncio.run(send_mail(db, mail_history_id))

    db.add(mail_history)
    db.flush()
    db.refresh(mail_history)

    if (
        mail_history.status == MailHistoryStatus.SENT
        and mail_history.process_status == MailHistoryProcessStatus.SUCCESS
    ):
        handle_next_step(db, mail_history)

    db.commit()


@celery.task(name="skip_mail")
def skip_mail(mail_history_id: int):
    print(f"Start task skip for mail history {mail_history_id}")
    db = Session(engine)
    mail_history = skip_mail_service(db, mail_history_id)

    db.add(mail_history)
    db.flush()
    db.refresh(mail_history)

    if (
        mail_history.status == MailHistoryStatus.SKIPPED
        and mail_history.process_status == MailHistoryProcessStatus.SUCCESS
    ):
        handle_next_step(db, mail_history)

    db.commit()


@celery.task(name="track_bounced_mail")
def track_bounced_mail(last_check_time_in_minute: int, maximum_interval_in_days: int):
    db = Session(engine)
    print("Start task track bounced mail in all sequences")
    return track_bounced_mail_service(
        db, last_check_time_in_minute, maximum_interval_in_days
    )


@celery.task(name="track_replied_mail")
def track_replied_mail(maximum_interval_in_days: int):
    db = Session(engine)
    print("Start task track replied mail in all sequence")
    return track_replied_mail_service(db, maximum_interval_in_days)


@celery.task(name="upsert_hubspot_user")
def upsert_hubspot_user():
    db = Session(engine)
    asyncio.run(upsert_user_from_hubspot_google_sheet(db))


@celery.task(name="resume_campaign_person")
def resume_campaign_person():
    db = Session(engine)
    resume_campaign_person_service(db)


# celery -A celery_worker call create_credit_daily
@celery.task(name="create_credit_daily")
def create_credit_daily():
    db = Session(engine)
    create_credit_service(db)


@celery.task(name="send_jobs_to_sqs")
def send_jobs_to_sqs():
    db = Session(engine)
    send_jobs_to_sqs_service(db)


# celery -A celery_worker call track_unresponsive_sequence_person
@celery.task(name="track_unresponsive_sequence_person")
def track_unresponsive_sequence_person():
    db = Session(engine)
    return tracking_unresponsive_person(db)


@celery.task(name="upload_sequence_contact")
def upload_sequence_contact(
    sequence_campaign_id: int,
    df: pd.DataFrame,
    import_id: int,
    is_last_chunk: bool,
    total: int,
    team_id: int,
):
    print(f"Start task upload sequence contact from file {import_id}")
    db = Session(engine)
    result = save_to_db(sequence_campaign_id, df, db, import_id, total, team_id)
    if result:
        print(f"Uploaded file id {import_id} catched an error: {result}")
    if is_last_chunk:
        print(f"Finish task upload sequence contact from file {import_id}")
    return result


@celery.task(name="upload_enrichment_item_from_file")
def upload_enrichment_item_from_file(
    enrichment_id: int,
    enrichment_file_id: int,
    user_id: int,
    column_json_mapping_dict: Dict,
    delimiter: str,
    method: Optional[str] = None,
):
    db = Session(engine)
    result = upload_enrichment_item_from_file_service(
        enrichment_id,
        enrichment_file_id,
        user_id,
        column_json_mapping_dict,
        db,
        delimiter,
        method,
    )
    handle_identify = result.get("handle_identify", False)
    if handle_identify:
        identify_enrichment.apply_async(
            (
                enrichment_id,
                user_id,
                None,
                None,
                enrichment_file_id,
            ),
        )
    else:
        db.exec(
            update(EnrichmentFile)
            .where(EnrichmentFile.id == enrichment_file_id)
            .values(upload_process_status=UploadProcessStatus.FAILED.value)
        )
        db.exec(
            update(Enrichment)
            .where(Enrichment.id == enrichment_id)
            .values(status=EnrichmentStatus.FAILED.value)
        )
    return True


@celery.task(name="identify_enrichment")
def identify_enrichment(
    enrichment_id: int,
    user_id: int,
    item_id_list: List[int] = None,
    is_last_chunk: Optional[bool] = None,
    enrichment_file_id: Optional[int] = None,
):
    db = Session(engine)
    return identify_enrichment_service(
        enrichment_id,
        user_id,
        item_id_list,
        is_last_chunk,
        enrichment_file_id,
        db,
    )


@celery.task(
    name="trigger_linkedin", bind=True, default_retry_delay=60, max_retries=None
)
def trigger_linkedin(
    self, mail_history_id: int, type: StepType, await_task_ids: List[int] = None
):
    db = Session(engine)
    redis_client = Redis(
        host=redis_host, port=int(redis_port), ssl=True, ssl_cert_reqs="none"
    )
    history = db.get(SequenceMailHistory, mail_history_id)
    if not history:
        print(f"No history found for id {mail_history_id}")
        return
    linkedin_account_id = history.sequence_linkedin_account_id
    redis_prefix = f"lock:linkedin_account_id_{linkedin_account_id}"
    if await_task_ids and len(await_task_ids) > 0:
        for task_id in await_task_ids:
            redis_key = f"{redis_prefix}:{task_id}"
            if redis_client.get(redis_key):
                raise self.retry(countdown=60)

    if type == StepType.LINKEDIN_VIEW_PROFILE:
        history = view_linkedin_profile_service(db, mail_history_id)
    elif type == StepType.LINKEDIN_AUTO_MESSAGE:
        history = send_linkedin_message_service(db, mail_history_id)
    elif type == StepType.LINKEDIN_CONNECTION_REQUEST:
        history = send_linkedin_connection_request_service(db, mail_history_id)

    time.sleep(10)
    linkedin_account = db.get(LinkedInAccount, linkedin_account_id)
    if linkedin_account:
        redis_client.setex(
            f"{redis_prefix}:{mail_history_id}",
            linkedin_account.request_interval_seconds,
            "1",
        )
    db.add(history)
    db.flush()
    db.refresh(history)
    if (
        history.status == MailHistoryStatus.SENT
        and history.process_status == MailHistoryProcessStatus.SUCCESS
    ):
        handle_next_step(db, history)
    db.commit()


@celery.task(name="cache_cross_search_first_steps")
def cache_cross_search_first_steps(
    query: dict,
    cache_key: str,
):
    es_client = AsyncElasticsearch(
        hosts=[es_url],
        http_auth=es_basic_auth,
        timeout=60,
    )
    redis_client = Redis(
        host=redis_host, port=int(redis_port), ssl=True, ssl_cert_reqs="none"
    )

    return asyncio.run(
        cache_cross_search_first_steps_service(
            es_client,
            redis_client,
            query,
            cache_key,
        )
    )


@celery.task(name="send_document_new_user")
def send_document_to_new_user():
    mail_from = EmailStr("sales@salessmart.jp")
    from_name = "トーマス（AMIRA HOLDINGS JSC）"
    db = Session(engine)
    mail_connection = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM=mail_from,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        MAIL_FROM_NAME=str(Header(from_name, "utf-8")),
        TEMPLATE_FOLDER=Path(__file__).parent.parent / "app/api/v1/templates",
    )
    asyncio.run(send_document_mail_to_new_user_service(db, mail_connection))


celery.conf.update(
    timezone="UTC",
    beat_schedule={
        "track-bounced-email": {
            "task": "track_bounced_mail",
            "schedule": crontab(minute="*/15"),  # Mỗi 15p 1 lần
            "args": (10, 14),
            "options": {
                "expires": 60 * 14,
                "soft_time_limit": 60 * 13,
                "time_limit": 60 * 14,
            },  # expires and time limit set to 14min
        },
        "track-replied-email": {
            "task": "track_replied_mail",
            "schedule": crontab(minute="*/15"),  # Mỗi 15p 1 lần
            "args": [14],
            "options": {
                "expires": 60 * 14,
                "soft_time_limit": 60 * 13,
                "time_limit": 60 * 14,
            },  # expires and time limit set to 14min
        },
        "upsert-hubspot-user": {
            "task": "upsert_hubspot_user",
            "schedule": crontab(minute="*/5"),  # Mỗi 5 phút
        },
        "resume-campaign-person": {
            "task": "resume_campaign_person",
            "schedule": crontab(minute="*/5"),  # Mỗi 5 phút
            "options": {"expires": 60 * 4},  # expires after 25 min
        },
        "create-credit-daily": {
            "task": "create_credit_daily",
            "schedule": crontab(
                minute=59,
                hour=23,
            ),  # crontab(minute=59, hour=23),  # Mỗi 1 ngay
        },
        "send-jobs-to-sqs": {
            "task": "send_jobs_to_sqs",
            "schedule": crontab(minute="*/5"),  # Mỗi 5 phút
        },
        "track_unresponsive_sequence_person": {
            "task": "track_unresponsive_sequence_person",
            "schedule": crontab(minute="*/30"),
        },
        "send-document-new-user": {
            "task": "send_document_new_user",
            "schedule": crontab(minute="*/5"),  # Mỗi 5 phút
        },
    },
)
