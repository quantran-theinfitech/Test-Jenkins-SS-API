import uuid
from typing import List

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.hubspot_connections import TypeSync
from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.db import engine
from app.models import HubspotCompanySyncHistories, HubspotIntergrations
from batch.common import IDENTIFY_ACTION_HANDLER, parse_arguments
from utils.identify.pull_person_identify import pull_person_identify


def hubspot_pull_persons(args: List[str]):
    print("_______ start func hubspot_pull_persons _______")
    try:
        arguments = parse_arguments(args)
        if "log_id" in arguments:
            handle_hubspot_pull_person(arguments["log_id"])
        else:
            db = Session(engine)
            hubspots = db.exec(
                select(HubspotIntergrations).where(
                    HubspotIntergrations.deleted_at.is_(None)
                )
            ).all()
            log_ids = []

            for hubspot in hubspots:
                if hubspot.auto_pull_persons:
                    try:
                        hubspot_company_sync = HubspotCompanySyncHistories(
                            hubspot_team_id=hubspot.hubspot_team_id,
                            integration_id=hubspot.id,
                            team_id=hubspot.team_id,
                            type=TypeSync.IDENTIFY_PERSON,
                            status=0,
                            hubspot_push_type="AUTO",
                            log_id=str(uuid.uuid4()),
                        )
                        db.add(hubspot_company_sync)
                        log_ids.append(hubspot_company_sync.log_id)
                        db.flush()
                    except HTTPException as e:
                        print(
                            "_______ error func hubspot_pull_persons (AUTO) _______",
                            str(e.detail),
                        )
                        continue
                else:
                    continue
            db.commit()
            for log_id in log_ids:
                try:
                    handle_hubspot_pull_person(log_id)
                except HTTPException as e:
                    print(
                        "_______ error log_id hubspot_pull_persons _______",
                        str(e.detail),
                    )
                    continue
    except HTTPException as e:
        print("_______ error func hubspot_pull_persons _______", str(e.detail))
        raise e


def handle_hubspot_pull_person(log_id: str):
    print("_______ start func handle_hubspot_pull_person _______")
    db = Session(engine)

    sync_history = db.exec(
        select(HubspotCompanySyncHistories).where(
            HubspotCompanySyncHistories.log_id == log_id
        )
    ).first()

    try:
        result = pull_person_identify(
            sync_history.integration_id,
            platform=INTEGRATION_PLATFORM_ENUM["HUBSPOT"],
        )

        print("_______ result _______", len(result))
        for item in result:
            IDENTIFY_ACTION_HANDLER[item.action](db, item, sync_history)

        sync_history.total_companies = len(result)
        sync_history.status = 1
        print("_______ pull_person_history _______", sync_history)
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
        print("_______ error of func handle_hubspot_pull_person _______", error)
        if db and sync_history:
            sync_history.status = 2
            sync_history.error_message = str(error)
            db.add(sync_history)
            db.commit()
        raise e
