from datetime import datetime
from enum import Enum

import boto3

from app.config import settings


class BatchManualAction(str, Enum):
    HUBSPOT_PULL_COMPANIES = "HUBSPOT_PULL_COMPANIES"
    HUBSPOT_PUSH_COMPANIES = "HUBSPOT_PUSH_COMPANIES"
    HUBSPOT_PULL_PERSONS = "HUBSPOT_PULL_PERSONS"
    HUBSPOT_SYNC_COMPANIES = "HUBSPOT_SYNC_COMPANIES"
    SALESFORCE_PULL_COMPANIES = "SALESFORCE_PULL_COMPANIES"
    SALESFORCE_PUSH_COMPANIES = "SALESFORCE_PUSH_COMPANIES"
    SALESFORCE_PULL_PERSONS = "SALESFORCE_PULL_PERSONS"
    SALESFORCE_SYNC_COMPANIES = "SALESFORCE_SYNC_COMPANIES"


MANUAL_TASK_MAPPING = {
    BatchManualAction.HUBSPOT_PUSH_COMPANIES: "hubspot_push_companies",
    BatchManualAction.HUBSPOT_PULL_COMPANIES: "hubspot_pull_companies",
    BatchManualAction.HUBSPOT_PULL_PERSONS: "hubspot_pull_persons",
    BatchManualAction.HUBSPOT_SYNC_COMPANIES: "hubspot_sync_companies",
    BatchManualAction.SALESFORCE_PUSH_COMPANIES: "salesforce_push_companies",
    BatchManualAction.SALESFORCE_PULL_COMPANIES: "salesforce_pull_companies",
    BatchManualAction.SALESFORCE_PULL_PERSONS: "salesforce_pull_persons",
    BatchManualAction.SALESFORCE_SYNC_COMPANIES: "salesforce_sync_companies",
}


class AWSBatchService:
    def __init__(self):
        self.client = boto3.client("batch")

    def submit_job_by_log_id(self, action: BatchManualAction, log_id: str):
        job_name = f"{action}_{int(datetime.timestamp(datetime.now()))}_manual_{log_id}"
        self.client.submit_job(
            jobName=job_name,
            jobQueue=settings.HUB_AWS_BATCH_JOB_QUEUE,
            jobDefinition=self.get_job_definition_arn(),
            containerOverrides={
                "command": [
                    "python",
                    "-m",
                    "batch.main",
                    MANUAL_TASK_MAPPING[action],
                    f"--log_id={log_id}",
                ],
            },
            tags={
                "manual": "true",
                "log_id": f"{log_id}",
            },
        )

    def get_job_definition_arn(self):
        response = self.client.describe_job_definitions(
            jobDefinitionName=settings.HUB_AWS_BATCH_JOB_DEFINITION,
            status="ACTIVE",
            maxResults=1,
        )
        if "jobDefinitions" not in response or len(response["jobDefinitions"]) == 0:
            raise Exception(
                f"NO JOB DEFINITION FOR NAME: {settings.HUB_AWS_BATCH_JOB_DEFINITION}"
            )
        return response["jobDefinitions"][0]["jobDefinitionArn"]
