import json
from datetime import datetime

import boto3
from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.scenarios import ScenarioMessage
from app.config import settings
from app.models.ingest import StateCode
from app.models.scenario import TypeCode
from app.models.team import PlanCode
from utils.chunk_string import chunk_lists

batch_client = boto3.Session(
    aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,
    aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY,
    region_name=settings.AWS_REGION_NAME,
).client("batch")


def listing_all_scenarios_with_notify(db: Session):
    query = """with last_subcriptions as (
        select team_id, max(expire_at) as max_expire_at
        from subcriptions ss
        group by team_id, plan_code
        having ss.plan_code = :pre_plan_code
        )
        select s.*, sc.url as target_slack from scenarios s
        left join teams t on t.id = s.team_id
        left join last_subcriptions ls on ls.team_id = s.team_id
        left join slack_connections sc
        on sc.id = s.target_slack_connection_id
        where t.listing_plan_code = :pre_plan_code
            and ls.max_expire_at >= 'now'
            and (s.slack_notification_flag = 'true'
            or s.email_notification_flag = 'true')
            and s.type_code = :recruit_scenario_code"""
    listing_scenarios = db.execute(
        text(query),
        params={
            "pre_plan_code": PlanCode.UNLIMITED,
            "recruit_scenario_code": TypeCode.RECRUIT,
        },
    ).all()

    return listing_scenarios


def notify_new_recruit(db: Session):
    update_in_db_query = """
                UPDATE ingests
                SET state = :processing_state_code
                WHERE state = :in_db_state_code
                RETURNING ingest_id;
            """
    ingest_ids = db.execute(
        text(update_in_db_query),
        params={
            "processing_state_code": StateCode.PROCESSING,
            "in_db_state_code": StateCode.IN_DB,
        },
    ).all()
    ingest_ids = [i[0] for i in ingest_ids]
    if len(ingest_ids) > 0:
        db.commit()
        listing_scenarios = listing_all_scenarios_with_notify(db)
        listing_scenarios = [
            json.dumps(
                ScenarioMessage(**x, ingest_ids=ingest_ids).__dict__, ensure_ascii=False
            )
            + " "
            for x in listing_scenarios
        ]
        chunks = chunk_lists(listing_scenarios, 15, 8192)
        job_name = "dev_sbapp_scenario_trigger_job_" + str(
            datetime.now().strftime("%Y%m%d%H%M%s")
        )
        for c in chunks:
            if len(c) > 1:
                batch_client.submit_job(
                    jobName=job_name,
                    jobQueue=settings.AWS_JOB_QUEUE,
                    jobDefinition=settings.AWS_JOB_DEFINITION,
                    arrayProperties={"size": len(c)},
                    containerOverrides={
                        "command": c,
                    },
                )
            else:
                batch_client.submit_job(
                    jobName=job_name,
                    jobQueue=settings.AWS_JOB_QUEUE,
                    jobDefinition=settings.AWS_JOB_DEFINITION,
                    containerOverrides={
                        "command": c,
                    },
                )
        update_processing_query = """
                    UPDATE ingests
                    SET state = :done_state_code
                    WHERE state = :processing_state_code
                        AND ingest_id IN :ingest_ids
                """
        db.execute(
            text(update_processing_query),
            params={
                "done_state_code": StateCode.DONE,
                "processing_state_code": StateCode.PROCESSING,
                "ingest_ids": tuple(ingest_ids),
            },
        )
        db.commit()
        return True
    else:
        return False
