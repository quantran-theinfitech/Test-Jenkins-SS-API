# flake8: noqa: E501
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from sqlmodel import Session, text

from app.config import settings

logger = logging.getLogger(__name__)


def _check_settings():
    """Check if all required settings are configured."""
    required_settings = [
        "MAX_VCPUS",
        "JOB_QUEUE",
        "JOB_DEFINITION",
        "JOB_NAME_PREFIX",
        "BUCKET_NAME",
        "HASHIDS_SALT",
        "PREFIX_TRACKING_URL",
        "DB_PORT",
        "DB_HOST",
        "DB_DATABASE",
        "DB_USERNAME",
        "DB_PASSWORD",
    ]
    missing_settings = [s for s in required_settings if not getattr(settings, s, None)]
    if missing_settings:
        raise ValueError(f"Missing required configurations: {missing_settings}")

    # Check TEST_MODE separately since 0 is a valid value
    if not hasattr(settings, "TEST_MODE"):
        raise ValueError("TEST_MODE setting is missing")


def _submit_batch_job(
    form_job_id: str,
    identifier: str,
    priority: int,
) -> Optional[str]:
    """Submit a job to AWS Batch and return the job ID."""
    logger.info("Submit job to AWS.")
    try:
        client = boto3.client("batch", region_name="ap-northeast-1")
        job_name_prefix = settings.JOB_NAME_PREFIX or "salesbox-form"
        job_name = (
            f"{job_name_prefix}_"
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{uuid4()}"
        )

        # URL-encode the database credentials
        if not settings.DB_USERNAME or not settings.DB_PASSWORD:
            raise ValueError("Database credentials are required")

        db_user_encoded = quote(str(settings.DB_USERNAME))
        # db_password_encoded = quote(str(settings.DB_PASSWORD))

        job_payload = {
            "jobName": job_name,
            "jobQueue": settings.JOB_QUEUE,
            "jobDefinition": settings.JOB_DEFINITION,
            "timeout": {"attemptDurationSeconds": 600},
            "containerOverrides": {
                "environment": [
                    {"name": "DB_PORT", "value": str(settings.DB_PORT)},
                    {"name": "FORM_JOB_ID", "value": form_job_id},
                    {"name": "DB_USER", "value": db_user_encoded},
                    {"name": "DB_HOST", "value": settings.DB_HOST},
                    {"name": "DB_DATABASE", "value": settings.DB_DATABASE},
                    {"name": "DB_PASSWORD", "value": settings.DB_PASSWORD},
                    {"name": "BUCKET_NAME", "value": settings.BUCKET_NAME},
                    {"name": "HASHIDS_SALT", "value": settings.HASHIDS_SALT},
                    {
                        "name": "PREFIX_TRACKING_URL",
                        "value": settings.PREFIX_TRACKING_URL,
                    },
                    {"name": "TEST_MODE", "value": settings.TEST_MODE},
                ],
                "resourceRequirements": [
                    {"value": "1", "type": "VCPU"},
                    {"value": "2048", "type": "MEMORY"},
                ],
            },
            "schedulingPriorityOverride": priority,
            "shareIdentifier": identifier,
        }

        response = client.submit_job(**job_payload)

        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info(
                f"Successfully submitted job {response['jobName']} "
                f"with ID {response['jobId']}"
            )
            return response["jobId"]

        logger.error(f"Failed to submit job. Response: {response}")
        return None
    except ClientError as e:
        logger.error(f"Error submitting job to AWS Batch: {e}", exc_info=True)
        return None


def _update_items_status(
    db: Session,
    item_ids: List[int],
    status: str,
    aws_batch_job_id: Optional[str] = None,
):
    """Update the status of form_job_items."""
    if not item_ids:
        return

    params = {"status_code": status, "item_ids": tuple(item_ids)}
    if aws_batch_job_id:
        query = text(
            """
            UPDATE form_job_items
            SET status_code = :status_code, aws_batch_id = :aws_batch_id
            WHERE id IN :item_ids
            """
        )
        params["aws_batch_id"] = aws_batch_job_id
    else:
        query = text(
            """
            UPDATE form_job_items
            SET status_code = :status_code
            WHERE id IN :item_ids
            """
        )
    db.execute(query, params)
    db.commit()


def _get_job_run_status_by_id(aws_batch_id: str) -> Optional[str]:
    """Get a job run by aws batch id."""
    client = boto3.client("batch", region_name="ap-northeast-1")
    response = client.describe_jobs(jobs=[aws_batch_id])
    if response["jobs"]:
        return response["jobs"][0]["status"]
    return None


def _update_form_job_status(db: Session, item_ids: List[int], status: str):
    """Update the status of a form_job."""
    if not item_ids:
        return
    params = {"status_code": status, "item_ids": tuple(set(item_ids))}
    query = text(
        """
        UPDATE form_jobs
        SET status_code = :status_code
        WHERE id IN :item_ids
        """
    )
    db.execute(query, params)
    db.commit()


def send_jobs_to_sqs_service(db: Session) -> Dict[str, Any]:
    """Fetches pending form jobs and submits them to AWS Batch."""
    logger.info("Starting send_jobs_to_sqs_service.")
    try:
        _check_settings()
    except ValueError as e:
        logger.error(f"Configuration check failed: {e}", exc_info=True)
        return {"statusCode": 400, "body": "Configuration error"}

    try:
        running_jobs = listing_form_job_items(db, "RUNNING")
        for job in running_jobs:
            if job["retry_count"] >= 1:
                _update_items_status(db, [job["id"]], "ERROR")
            else:
                job_run_status = _get_job_run_status_by_id(job["aws_batch_id"])
                if job_run_status == "FAILED":
                    _update_items_status(db, [job["id"]], "PENDING")
                    db.execute(
                        text(
                            """
                        UPDATE form_job_items
                        SET retry_count = retry_count + 1
                        WHERE id = :id
                        """
                        ),
                        {"id": job["id"]},
                    )
                    db.commit()

        form_job_items = listing_form_job_items(db, "PENDING")

        if not form_job_items:
            logger.info("No pending form jobs found.")
            return {"statusCode": 200, "body": "No pending jobs"}

        logger.info(f"Found {len(form_job_items)} form jobs to process.")
        _update_items_status(
            db, [form_job_item["id"] for form_job_item in form_job_items], "QUEUED"
        )
        logger.info("Update status form job items.")

        _update_form_job_status(
            db, [item["form_job_id"] for item in form_job_items], "RUNNING"
        )
        logger.info("Update status form job.")

        logger.info("Start submit job to AWS.")
        for i, item in enumerate(form_job_items):
            if not item["form_url"]:
                logger.warning(
                    f"Form URL is missing for item ID {item['id']}. Skipping submission"
                )
                _update_items_status(db, [item["id"]], "NOT_SEND")
                continue
            count = 0
            success = False
            while not success and count < 3:
                try:
                    priority = max(1, 9999 - i)
                    aws_batch_job_id = _submit_batch_job(
                        str(item["id"]), f"formjob{i}", priority
                    )
                    if aws_batch_job_id:
                        _update_items_status(
                            db, [item["id"]], "RUNNING", aws_batch_job_id
                        )
                        success = True
                        form_job = get_form_job_by_id(db, item["form_job_id"])
                        if form_job and (
                            form_job["status_code"] == "QUEUED"
                            or form_job["status_code"] == "PENDING"
                        ):
                            _update_form_job_status(
                                db, [item["form_job_id"]], "RUNNING"
                            )

                except Exception as e:
                    count += 1
                    if count >= 3:
                        logger.error(
                            f"Failed to process form job items after 3 attempts: {e}",
                            exc_info=True,
                        )
                        _update_items_status(db, [item["id"]], "PENDING")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred in send_jobs_to_sqs_service: {e}",
            exc_info=True,
        )
        return {"statusCode": 500, "body": "Internal server error"}

    logger.info("Finished send_jobs_to_sqs_service successfully.")
    return {"statusCode": 200, "body": "Success"}


def listing_form_job_items(db: Session, status_code: str):
    # Get placeholder, template of form jobs and form job info from status
    listing_form_job_items_query = """
        SELECT fji.id, fj.id as form_job_id, fji.form_url, fji.aws_batch_id, fji.retry_count
        FROM form_job_items fji
        INNER JOIN form_jobs fj
        ON fj.id = fji.job_id
        LEFT JOIN team_companies tc
        ON tc.corporate_number = fji.corporate_number
        WHERE fj.schedule_at <= now()
        AND fji.status_code = :status_code
        AND tc.status_code != 'APPROACH_NG'
        GROUP BY fji.id, fj.schedule_at, fj.id
        ORDER BY fj.schedule_at, fji.created_at;
    """
    return db.execute(
        text(listing_form_job_items_query), {"status_code": status_code}
    ).all()


def get_form_job_by_id(db: Session, form_job_id: int):
    """Fetch a form job by its ID."""
    query = text(
        """
        SELECT *
        FROM form_jobs
        WHERE id = :form_job_id
        """
    )
    return db.execute(query, {"form_job_id": form_job_id}).first()
