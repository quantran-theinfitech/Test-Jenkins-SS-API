import sqlalchemy
from elasticsearch_dsl import Q, Search, UpdateByQuery
from sqlmodel import Session, select

from app.api.base.exceptions import ConflictException, PaymentRequiredException
from app.api.v1.queries.company import build_es_query
from app.api.v1.schemas.companies import DownloadCompanyMode
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from utils.credit_utils import is_enough_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models import DownloadedHistory, Team, TeamCompany
from app.models.team import PlanCode
from app.models.team_company import StatusCode
from app.models.team_credit import ServiceCode


def download_all_companies(
    db: Session,
    es_client,
    current_user: UserBase,
    search_condition: SearchCrossRequest,
    mode: DownloadCompanyMode,
):
    team = db.exec(select(Team).where(Team.id == current_user.team_id)).one()

    if team.listing_plan_code == PlanCode.UNLIMITED:
        raise ConflictException(detail="company.companyHasAlreadyDownloaded")

    corporate_numbers_downloaded = (
        db.execute(
            sqlalchemy.select(TeamCompany.corporate_number).where(
                TeamCompany.team_id == current_user.team_id
            )
        )
        .scalars()
        .all()
    )

    search_query = build_es_query(search_condition)
    queries = []
    queries.append(search_query)
    queries.append(Q("bool", must_not=Q("term", team_ids=current_user.team_id)))
    if corporate_numbers_downloaded:
        queries.append(
            Q(
                "bool",
                must_not=Q("terms", corporate_number=corporate_numbers_downloaded),
            )
        )
    download_query = Q("bool", must=queries)

    search = Search(using=es_client, index=EsCompanyExtend.Index.name)
    search = search.query(download_query)
    search = search.source(["corporate_number"])
    pagination_param = {
        "size": 0,  # Just get the total, no data needed
        "from": 0,
    }
    total_corporate_numbers_will_download = (
        search.extra(**pagination_param).execute()["hits"]._d_["total"]["value"]
    )

    amount_will_spend = (
        settings.AMOUNT_PER_DOWNLOAD * total_corporate_numbers_will_download
    )

    if not is_enough_credit(db, current_user.team_id, amount_will_spend):
        if mode is DownloadCompanyMode.EXACT:
            raise PaymentRequiredException(
                detail={
                    "message": "company.notEnoughCredit",
                    "remaining_credit": remaining_credit(db, current_user.team_id),
                }
            )
        elif mode is DownloadCompanyMode.RANDOM:
            total_corporate_numbers_will_download = int(
                remaining_credit(db, current_user.team_id)
                / settings.AMOUNT_PER_DOWNLOAD
            )
            total_corporate_numbers_will_download = (
                total_corporate_numbers_will_download
                if total_corporate_numbers_will_download > 0
                else 0
            )
            amount_will_spend = (
                settings.AMOUNT_PER_DOWNLOAD * total_corporate_numbers_will_download
            )

    if total_corporate_numbers_will_download == 0:
        return total_corporate_numbers_will_download

    if total_corporate_numbers_will_download > 10000:
        raise ConflictException(detail="common.hasTooManyCompanies")

    try:
        pagination_param = {"size": total_corporate_numbers_will_download}
        result = search.extra(**pagination_param).execute()["hits"]
        data = result["hits"]._l_
        corporate_numbers = [x["_source"]["corporate_number"] for x in data]
        team_companies = [
            TeamCompany(
                team_id=current_user.team_id,
                corporate_number=x,
                status_code=StatusCode.PENDING,
            )
            for x in corporate_numbers
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

        update_query = Q("terms", corporate_number=corporate_numbers)
        ubq = UpdateByQuery(
            using=es_client, index=EsCompanyExtend.Index.name
        )  # config settings for es update by query
        ubq = ubq.script(
            source="""
                if(ctx._source.team_ids==null) ctx._source.team_ids = [params.team_id];
                else ctx._source.team_ids.add(params.team_id);
                """,
            lang="painless",
            params={"team_id": current_user.team_id},
        )  # config settings for es update by query
        ubq.query(update_query).execute()  # execute es update by query
    except Exception as e:
        db.rollback()
        raise e

    return total_corporate_numbers_will_download
