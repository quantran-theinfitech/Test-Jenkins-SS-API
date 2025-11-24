import uuid
from typing import List

from fastapi import HTTPException
from sqlmodel import Session, select

from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.db import engine
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    TYPE_INTEGRATION_ENUM,
    SalesforceSyncHistories,
)
from batch.common import IDENTIFY_ACTION_HANDLER, parse_arguments
from utils.identify.pull_identify import pull_identify


def salesforce_pull_companies(args: List[str]):
    print("_______ start func salesforce_pull_companies _______")
    try:
        arguments = parse_arguments(args)
        if "log_id" in arguments:
            handle_salesforce_pull_companies(arguments["log_id"])
        else:
            db = Session(engine)
            salesforces = db.exec(
                select(SalesforceIntegrations).where(
                    SalesforceIntegrations.deleted_at.is_(None)
                )
            ).all()
            log_ids = []

            for salesforce in salesforces:
                if salesforce.auto_pull_companies:
                    try:
                        salesforce_company_sync = SalesforceSyncHistories(
                            salesforce_team_id=salesforce.salesforce_team_id,
                            salesforce_integration_id=salesforce.id,
                            team_id=salesforce.team_id,
                            type=TYPE_INTEGRATION_ENUM.PULL_COMPANIES,
                            status=0,
                            method="AUTO",
                            log_id=str(uuid.uuid4()),
                        )
                        db.add(salesforce_company_sync)
                        log_ids.append(salesforce_company_sync.log_id)
                        db.flush()
                    except HTTPException as e:
                        print(
                            "_______ error salesforce_pull_companies (AUTO) _______",
                            str(e.detail),
                        )
                        continue
                else:
                    continue
            db.commit()
            for log_id in log_ids:
                try:
                    handle_salesforce_pull_companies(log_id)
                except HTTPException as e:
                    print(
                        "_______ error log_id salesforce_pull_companies _______",
                        str(e.detail),
                    )
                    continue
    except HTTPException as e:
        print("_______ error func salesforce_pull_companies _______", str(e.detail))
        raise e


def handle_salesforce_pull_companies(log_id: str):
    print("_______ start func handle_salesforce_pull_companies _______")
    db = Session(engine)

    sync_history = db.exec(
        select(SalesforceSyncHistories).where(
            SalesforceSyncHistories.log_id == log_id,
        )
    ).first()

    try:
        result = pull_identify(
            integration_id=sync_history.salesforce_integration_id,
            platform=INTEGRATION_PLATFORM_ENUM["SALESFORCE"],
        )

        print("_______ result _______", len(result))

        for item in result:
            IDENTIFY_ACTION_HANDLER[item.action](db, item, sync_history)

        sync_history.total_companies = len(result)
        sync_history.status = 1
        print("_______ pull_history _______", sync_history)
        db.add(sync_history)
        db.commit()
    except HTTPException as e:
        error = None
        if hasattr(e, "content"):
            error = e.content
        elif hasattr(e, "body"):
            error = e.body
        elif hasattr(e, "detail"):
            error = e.detail
        elif hasattr(e, "response") and hasattr(e.response, "text"):
            error = e.response.text
        else:
            error = str(e)
        print("_______ error of func handle_salesforce_pull_companies _______", error)
        if db and sync_history:
            sync_history.status = 2
            sync_history.error_message = str(error)
            db.add(sync_history)
            db.commit()
        raise e
