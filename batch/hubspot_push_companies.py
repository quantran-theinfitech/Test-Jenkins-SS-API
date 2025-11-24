from typing import List

from fastapi import HTTPException
from sqlmodel import Session, and_, select

from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.db import engine
from app.models.company import Company
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_manual_push_companies import (
    HubspotManualPushCompanies,
)
from batch.common import IDENTIFY_ACTION_HANDLER, parse_arguments
from utils.identify.push_identify import push_identify


def hubspot_push_companies(args: List[str]):
    print(
        "_______ start func hubspot_push_companies _______",
    )
    try:
        arguments = parse_arguments(args)
        if "log_id" in arguments:
            handle_hubspot_push_companies(arguments["log_id"])
        else:
            # create new SyncHistory log_id and call handler
            pass
    except HTTPException as e:
        print("_______ error of func hubspot_push_companies _______", str(e))
        raise e


def handle_hubspot_push_companies(log_id: str):
    print("_______ start func handle_hubspot_push_companies _______")
    db = Session(engine)

    sync_history = db.exec(
        select(HubspotCompanySyncHistories).where(
            HubspotCompanySyncHistories.log_id == log_id
        )
    ).first()

    try:
        companies = db.exec(
            select(Company)
            .join(
                HubspotManualPushCompanies,
                and_(
                    Company.corporate_number == HubspotManualPushCompanies.company_id,
                    HubspotManualPushCompanies.deleted_at.is_(None),
                ),
            )
            .where(HubspotManualPushCompanies.log_id == log_id)
        ).all()

        result = push_identify(
            integration_id=sync_history.integration_id,
            ss_company_ids=[
                c.corporate_number for c in companies if c.corporate_number is not None
            ],
            platform=INTEGRATION_PLATFORM_ENUM["HUBSPOT"],
        )

        print("_______ result _______", len(result))
        for item in result:
            IDENTIFY_ACTION_HANDLER[item.action](db, item, sync_history)

        sync_history.total_companies = len(result)
        sync_history.status = 1
        print("_______ push_history _______", sync_history)
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
        print("_______ error of func handle_hubspot_push_companies _______", error)
        if db and sync_history:
            sync_history.status = 2
            sync_history.error_message = str(error)
            db.add(sync_history)
            db.commit()
        raise e
