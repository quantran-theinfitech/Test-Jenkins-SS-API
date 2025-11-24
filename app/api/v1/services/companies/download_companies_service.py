from typing import List

import sqlalchemy
from elasticsearch import ConflictError
from elasticsearch_dsl import Q, UpdateByQuery
from sqlmodel import Session, col, select

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    PaymentRequiredException,
)
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from utils.credit_utils import is_enough_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models import DownloadedHistory, Team, TeamCompany
from app.models.team import PlanCode
from app.models.team_company import StatusCode
from app.models.team_credit import ServiceCode


def download_companies(
    db: Session, es_client, current_user: UserBase, corporate_numbers: List[str]
):
    if len(corporate_numbers) > 10000:
        raise BadRequestException(detail="company.tooManyCompanies")
    team = db.exec(select(Team).where(Team.id == current_user.team_id)).one()

    if team.listing_plan_code == PlanCode.UNLIMITED:
        raise ConflictException(detail="company.companyHasAlreadyDownloaded")

    corporate_numbers_downloaded = (
        db.execute(
            sqlalchemy.select(TeamCompany.corporate_number)
            .where(col(TeamCompany.corporate_number).in_(corporate_numbers))
            .where(TeamCompany.team_id == current_user.team_id)
        )
        .scalars()
        .all()
    )
    corporate_numbers_will_download = [
        x for x in corporate_numbers if x not in corporate_numbers_downloaded
    ]

    amount_will_spend = settings.AMOUNT_PER_DOWNLOAD * len(
        corporate_numbers_will_download
    )

    if not is_enough_credit(db, current_user.team_id, amount_will_spend):
        raise PaymentRequiredException(
            detail={
                "message": "company.notEnoughCredit",
                "remaining_credit": remaining_credit(db, current_user.team_id),
            }
        )

    try:
        team_companies = [
            TeamCompany(
                team_id=current_user.team_id,
                corporate_number=x,
                status_code=StatusCode.PENDING,
            )
            for x in corporate_numbers_will_download
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

        if len(corporate_numbers_will_download) > 0:
            ubq = UpdateByQuery(using=es_client, index=EsCompanyExtend.Index.name)
            update_query = Q("terms", corporate_number=corporate_numbers_will_download)
            ubq = ubq.query(update_query).script(
                source="""
                if(ctx._source.team_ids==null) ctx._source.team_ids = [params.team_id];
                else ctx._source.team_ids.add(params.team_id);
                """,
                lang="painless",
                params={"team_id": current_user.team_id},
            )
            ubq.params(refresh="wait_for")
            ubq.params(retry_on_conflict=3)
            try:
                ubq.execute()
            except ConflictError:
                pass

    except Exception as e:
        db.rollback()
        raise e

    return corporate_numbers_will_download
