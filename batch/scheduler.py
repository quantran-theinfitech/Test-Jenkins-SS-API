"""
Batch Scheduler Service
Chạy các batch jobs sử dụng APScheduler
Tương tự Celery beat nhưng không cần Celery
"""

import logging
from pathlib import Path

import sentry_sdk
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from batch.hubspot_pull_companies import hubspot_pull_companies
from batch.hubspot_sync_companies import hubspot_sync_companies
from batch.salesforce_pull_companies import salesforce_pull_companies
from batch.salesforce_sync_companies import salesforce_sync_companies
from batch.sequence_schedule_tasks import handle_sequence_schedule_tasks

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "batch_scheduler.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),  # Vẫn log ra console
    ],
)

logger = logging.getLogger(__name__)

# Danh sách batch functions chạy vào 0h mỗi ngày
DAILY_BATCH_FUNCTIONS = [
    ("hubspot_sync_companies", hubspot_sync_companies),
    ("salesforce_sync_companies", salesforce_sync_companies),
    ("hubspot_pull_companies", hubspot_pull_companies),
    ("salesforce_pull_companies", salesforce_pull_companies),
]

# Batch function chạy mỗi 15 phút
PERIODIC_BATCH_FUNCTIONS = [
    ("handle_sequence_schedule_task", handle_sequence_schedule_tasks),
]


def init_sentry():
    """Initialize Sentry for error tracking"""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            send_default_pii=True,
            traces_sample_rate=1.0,
            profile_session_sample_rate=1.0,
            profile_lifecycle="trace",
            environment=settings.SENTRY_ENV,
        )


def run_batch_job(job_name: str, job_func):
    """Wrapper function để chạy batch job với error handling và logging"""
    logger.info(f"START BATCH JOB: {job_name}")
    try:
        with sentry_sdk.start_transaction(name=job_name, op="batch_job") as transaction:
            # Tất cả batch functions đều nhận args: List[str]
            # Truyền list rỗng vì chạy tự động không có arguments
            job_func([])
            transaction.set_status("ok")
        logger.info(f"FINISH BATCH JOB: {job_name} - SUCCESS")
    except Exception as e:
        logger.error(f"ERROR BATCH JOB: {job_name} - {str(e)}", exc_info=True)
        sentry_sdk.capture_exception(e)
        raise


def setup_scheduler():
    """Setup và start scheduler"""
    init_sentry()

    logger.info(f"Batch Scheduler initializing...")
    logger.info(f"Log file: {LOG_FILE.absolute()}")

    scheduler = BlockingScheduler(timezone="UTC")

    # Thêm các batch jobs chạy vào 0h mỗi ngày
    for job_name, job_func in DAILY_BATCH_FUNCTIONS:
        scheduler.add_job(
            func=run_batch_job,
            trigger=CronTrigger(hour=0, minute=0),  # 0h mỗi ngày
            args=[job_name, job_func],
            id=f"batch_{job_name}",
            name=f"Batch Job: {job_name}",
            replace_existing=True,
            max_instances=1,  # Chỉ cho phép 1 instance chạy cùng lúc
        )
        logger.info(f"Registered batch job: {job_name} - Schedule: 0:00 UTC daily")

    # Thêm batch job chạy mỗi 15 phút
    # Không giới hạn max_instances để cho phép nhiều instance chạy song song
    for job_name, job_func in PERIODIC_BATCH_FUNCTIONS:
        scheduler.add_job(
            func=run_batch_job,
            trigger=CronTrigger(minute="*/15"),  # Mỗi 15 phút
            args=[job_name, job_func],
            id=f"batch_{job_name}",
            name=f"Batch Job: {job_name}",
            replace_existing=True,
            # Không set max_instances để cho phép nhiều instance chạy song song
        )
        logger.info(
            f"Registered batch job: {job_name} - Schedule: Every 15 minutes (unlimited instances)"
        )

    total_jobs = len(DAILY_BATCH_FUNCTIONS) + len(PERIODIC_BATCH_FUNCTIONS)
    logger.info(f"Batch Scheduler started")
    logger.info(f"Total jobs registered: {total_jobs}")
    logger.info(f"  - {len(DAILY_BATCH_FUNCTIONS)} jobs scheduled at 0:00 UTC daily")
    logger.info(f"  - {len(PERIODIC_BATCH_FUNCTIONS)} job scheduled every 15 minutes")
    logger.info("Press Ctrl+C to stop the scheduler")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Batch Scheduler stopped")
        scheduler.shutdown()


if __name__ == "__main__":
    setup_scheduler()
