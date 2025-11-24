import sqlalchemy
from elasticsearch_dsl import Q, Search, UpdateByQuery
from sqlmodel import Session

from app.api.base.exceptions import ConflictException, PaymentRequiredException
from app.api.v1.queries.person import build_es_query
from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.persons import DownloadPersonMode
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from utils.credit_utils import is_enough_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models import DownloadedHistory, TeamPerson
from app.models.team import PlanCode
from app.models.team_credit import ServiceCode


def download_all_persons(
    db: Session,
    es_client,
    current_user: UserBase,
    listing_plan_code: PlanCode,
    search_condition: SearchCrossRequest,
    mode: DownloadPersonMode,
):
    if listing_plan_code == PlanCode.UNLIMITED:
        raise ConflictException(detail="person.personHasAlreadyDownloaded")
    person_uuids_downloaded = db.execute(
        sqlalchemy.select(TeamPerson.person_uuid).where(
            TeamPerson.team_id == current_user.team_id
        )
    ).scalars()
    search_query = build_es_query(search_condition)
    queries = []
    queries.append(search_query)
    queries.append(Q("bool", must_not=Q("term", team_ids=current_user.team_id)))
    if person_uuids_downloaded:
        queries.append(
            Q(
                "bool",
                must_not=Q("terms", uuid=person_uuids_downloaded),
            )
        )
    download_query = Q("bool", must=queries)

    search = Search(using=es_client, index=ESPersonExtend.Index.name)
    search = search.query(download_query)
    search = search.source(["uuid"])
    pagination_param = {
        "size": 0,  # Just get the total, no data needed
        "from": 0,
    }
    total_person_uuids_will_download = (
        search.extra(**pagination_param).execute()["hits"]._d_["total"]["value"]
    )

    amount_will_spend = settings.AMOUNT_PER_DOWNLOAD * total_person_uuids_will_download

    if not is_enough_credit(
        db, current_user.team_id, amount_will_spend, service_code=ServiceCode.PERSON
    ):
        if mode is DownloadPersonMode.EXACT:
            raise PaymentRequiredException(
                detail={
                    "message": "person.notEnoughCredit",
                    "remaining_credit": remaining_credit(
                        db, current_user.team_id, service_code=ServiceCode.PERSON
                    ),
                }
            )
        elif mode is DownloadPersonMode.RANDOM:
            total_person_uuids_will_download = int(
                remaining_credit(
                    db, current_user.team_id, service_code=ServiceCode.PERSON
                )
                / settings.AMOUNT_PER_DOWNLOAD
            )
            total_person_uuids_will_download = (
                total_person_uuids_will_download
                if total_person_uuids_will_download > 0
                else 0
            )
            amount_will_spend = (
                settings.AMOUNT_PER_DOWNLOAD * total_person_uuids_will_download
            )

    if total_person_uuids_will_download == 0:
        return total_person_uuids_will_download

    if total_person_uuids_will_download > 10000:
        raise ConflictException(detail="common.hasTooManyPersons")

    try:
        pagination_param = {"size": total_person_uuids_will_download}
        result = search.extra(**pagination_param).execute()["hits"]
        data = result["hits"]._l_
        person_uuids = [x["_source"]["uuid"] for x in data]
        team_persons = [
            TeamPerson(
                team_id=current_user.team_id,
                person_uuid=x,
            )
            for x in person_uuids
        ]
        db.bulk_save_objects(team_persons)
        db.flush()

        downloaded_histories = DownloadedHistory(
            user_id=current_user.id,
            amount=amount_will_spend,
            service_code=ServiceCode.PERSON,
        )
        db.add(downloaded_histories)
        db.commit()
        consume_credit(
            db,
            current_user.team_id,
            amount_will_spend,
            service_code=ServiceCode.PERSON,
        )

        update_query = Q("terms", uuid=person_uuids)
        ubq = UpdateByQuery(
            using=es_client, index=ESPersonExtend.Index.name
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

    return total_person_uuids_will_download
