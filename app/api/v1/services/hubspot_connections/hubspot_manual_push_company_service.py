import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import (
    ConflictException,
    NotFoundException,
    PaymentRequiredException,
)
from app.api.v1.schemas.hubspot_connections import (
    HubspotManualPushCompanyRequest,
    TypePush,
    TypeSync,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models import DownloadedHistory, TeamCompany
from app.models.company import Company
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from app.models.integration.hubspot.hubspot_manual_push_companies import (
    HubspotManualPushCompanies,
)
from app.models.integration.hubspot.hubspot_synced_companies import (
    HubspotSyncedCompanies,
)
from app.models.team import PlanCode
from app.models.team_company import StatusCode
from app.models.team_credit import ServiceCode
from batch.aws_batch import AWSBatchService, BatchManualAction
from utils.credit_utils import is_enough_credit
from utils.hubspot_connection import HubSpotService


def hubspot_manual_push_company(
    db: Session,
    current_user: UserBase,
    request: HubspotManualPushCompanyRequest,
    listing_plan_code: PlanCode,
):
    if listing_plan_code is PlanCode.UNLIMITED:
        corporate_numbers_downloaded = request.corporate_numbers
    else:
        corporate_numbers_downloaded = get_list_company_download(
            db,
            current_user,
            request.type_push,
            request.corporate_numbers,
        )

    try:
        hubspot_intergration = db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.team_id == current_user.team_id,
                HubspotIntergrations.deleted_at.is_(None),
            )
        ).first()

        if not hubspot_intergration:
            raise NotFoundException(detail="common.notFound")

        hubspot_client = HubSpotService(
            access_token=hubspot_intergration.access_token,
            refresh_token=hubspot_intergration.refresh_token,
        )

        hubspot_company_sync = HubspotCompanySyncHistories(
            hubspot_team_id=hubspot_intergration.hubspot_team_id,
            integration_id=hubspot_intergration.id,
            team_id=current_user.team_id,
            type=TypeSync.PUSH_TO_HUBSPOT,
            status=0,
            hubspot_push_type="MANUAL",
            log_id=str(uuid.uuid4()),
        )

        db.add(hubspot_company_sync)
        db.flush()

        hubspot_manual_push_companies = []
        all_companies_hubspot = hubspot_client.get_all_companies() or []
        all_companies_hubspot_ids = [company.id for company in all_companies_hubspot]
        for company_id in corporate_numbers_downloaded or []:
            hubspot_synced_companies_detail = db.exec(
                select(HubspotSyncedCompanies).where(
                    HubspotSyncedCompanies.ss_company_id == company_id,
                    HubspotSyncedCompanies.deleted_at.is_(None),
                    HubspotSyncedCompanies.integration_id == hubspot_intergration.id,
                )
            ).first()

            if hubspot_synced_companies_detail:
                if (
                    hubspot_synced_companies_detail.hubspot_company_id
                    and hubspot_synced_companies_detail.hubspot_company_id
                    in all_companies_hubspot_ids
                ):
                    continue
                else:
                    hubspot_synced_companies_detail.deleted_at = datetime.now()
                    db.add(hubspot_synced_companies_detail)

            company = db.exec(
                select(Company).where(Company.corporate_number == company_id)
            ).first()

            if not company:
                raise NotFoundException(detail="common.notFoundCompany")

            hubspot_manual_push_companies.append(
                HubspotManualPushCompanies(
                    log_id=hubspot_company_sync.log_id,
                    company_id=company_id,
                )
            )

        if len(hubspot_manual_push_companies) > 0:
            db.add_all(hubspot_manual_push_companies)
            db.commit()

            batch = AWSBatchService()
            batch.submit_job_by_log_id(
                BatchManualAction.HUBSPOT_PUSH_COMPANIES, hubspot_company_sync.log_id
            )

        return True
    except HTTPException as e:
        db.rollback()
        print("_______ e _______", e)
        print("_______ error hubspot_manual_push_company _______", str(e.detail))
        raise e


def get_list_company_download(
    db: Session,
    current_user: UserBase,
    type_push: TypePush,
    list_corporate_numbers_download,
):
    corporate_numbers_downloaded = (
        db.execute(
            select(TeamCompany.corporate_number)
            .where(
                TeamCompany.team_id == current_user.team_id,
                TeamCompany.corporate_number.in_(list_corporate_numbers_download),
            )
            .distinct(TeamCompany.corporate_number)
        )
        .scalars()
        .all()
    )
    if type_push == TypePush.CREDIT.value:
        lock_company = [
            item
            for item in list_corporate_numbers_download
            if item not in corporate_numbers_downloaded
        ]
        amount_will_spend = settings.AMOUNT_PER_DOWNLOAD * len(lock_company)
        if not is_enough_credit(db, current_user.team_id, amount_will_spend):
            raise PaymentRequiredException(
                detail={
                    "message": "company.notEnoughCredit",
                    "remaining_credit": remaining_credit(db, current_user.team_id),
                }
            )
        if len(lock_company) > 10000:
            raise ConflictException(detail="common.hasTooManyCompanies")
        try:
            team_companies = [
                TeamCompany(
                    team_id=current_user.team_id,
                    corporate_number=x,
                    status_code=StatusCode.PENDING,
                )
                for x in lock_company
            ]
            db.bulk_save_objects(team_companies)
            db.flush()

            downloaded_histories = DownloadedHistory(
                user_id=current_user.id,
                amount=amount_will_spend,
                service_code=ServiceCode.CPN,
            )
            db.add(downloaded_histories)
            db.commit()
            consume_credit(
                db,
                current_user.team_id,
                amount_will_spend,
                service_code=ServiceCode.CPN,
            )
        except HTTPException as e:
            db.rollback()
            raise e
        return list_corporate_numbers_download

    return corporate_numbers_downloaded
