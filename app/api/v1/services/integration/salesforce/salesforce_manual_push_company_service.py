import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import (
    ConflictException,
    NotFoundException,
    PaymentRequiredException,
)
from app.api.v1.schemas.hubspot_connections import TypePush
from app.api.v1.schemas.integration.salesforce import SalesforceManualPushCompanyRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models.company import Company
from app.models.downloaded_histories import DownloadedHistory
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_manual_push_companies import (
    SalesforceManualPushCompanies,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    TYPE_INTEGRATION_ENUM,
    SalesforceSyncHistories,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from app.models.team import PlanCode
from app.models.team_company import StatusCode, TeamCompany
from app.models.team_credit import ServiceCode
from batch.aws_batch import AWSBatchService, BatchManualAction
from utils.credit_utils import is_enough_credit
from utils.integration.salesforce import SalesforceService


def salesforce_manual_push_companies(
    db: Session,
    current_user: UserBase,
    request: SalesforceManualPushCompanyRequest,
    listing_plan_code: PlanCode,
):
    try:
        if listing_plan_code is PlanCode.UNLIMITED:
            corporate_numbers_downloaded = request.corporate_numbers
        else:
            corporate_numbers_downloaded = get_list_company_download(
                db,
                current_user,
                request.type_push,
                request.corporate_numbers,
            )

        salesforce_connection = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.team_id == current_user.team_id,
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()

        if not salesforce_connection:
            raise NotFoundException(detail="common.notFound")

        salesforce_service = SalesforceService(
            access_token=salesforce_connection.access_token,
            refresh_token=salesforce_connection.refresh_token,
            instance_url=salesforce_connection.instance_url,
            id_url=salesforce_connection.id_url,
        )

        salesforce_sync = SalesforceSyncHistories(
            salesforce_team_id=salesforce_connection.salesforce_team_id,
            salesforce_integration_id=salesforce_connection.id,
            team_id=current_user.team_id,
            type=TYPE_INTEGRATION_ENUM.PUSH_COMPANIES,
            status=0,
            method="MANUAL",
            log_id=str(uuid.uuid4()),
        )

        db.add(salesforce_sync)
        db.flush()

        salesforce_manual_push_companies = []
        all_companies_salesforce = salesforce_service.get_all_companies(["Id"])
        all_companies_salesforce_ids = [
            company["Id"] for company in all_companies_salesforce
        ]

        for company_id in corporate_numbers_downloaded:
            salesforce_synced_companies_detail = db.exec(
                select(SalesforceSyncedCompanies).where(
                    SalesforceSyncedCompanies.ss_company_id == company_id,
                    SalesforceSyncedCompanies.deleted_at.is_(None),
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == salesforce_connection.id,
                )
            ).first()

            if salesforce_synced_companies_detail:
                if (
                    salesforce_synced_companies_detail.salesforce_company_id
                    and salesforce_synced_companies_detail.salesforce_company_id
                    in all_companies_salesforce_ids
                ):
                    continue
                else:
                    salesforce_synced_companies_detail.deleted_at = datetime.now()
                    db.add(salesforce_synced_companies_detail)

            company = db.exec(
                select(Company).where(Company.corporate_number == company_id)
            ).first()

            if not company:
                raise NotFoundException(detail="common.notFoundCompany")

            salesforce_manual_push_companies.append(
                SalesforceManualPushCompanies(
                    log_id=salesforce_sync.log_id,
                    ss_company_id=company_id,
                )
            )

        if len(salesforce_manual_push_companies) > 0:
            db.add_all(salesforce_manual_push_companies)
            db.commit()

            batch = AWSBatchService()
            batch.submit_job_by_log_id(
                BatchManualAction.SALESFORCE_PUSH_COMPANIES, salesforce_sync.log_id
            )
    except HTTPException as e:
        db.rollback()
        print("_______ error salesforce_manual_push_company _______", str(e))
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
