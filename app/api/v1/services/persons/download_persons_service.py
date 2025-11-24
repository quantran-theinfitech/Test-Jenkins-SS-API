from typing import List

import sqlalchemy
from elasticsearch import ConflictError
from elasticsearch_dsl import Q, UpdateByQuery
from sqlmodel import Session, col

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    PaymentRequiredException,
)
from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from utils.credit_utils import is_enough_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models import DownloadedHistory, TeamPerson
from app.models.team import PlanCode
from app.models.team_credit import ServiceCode


def download_persons(
    db: Session,
    es_client,
    current_user: UserBase,
    listing_plan_code: PlanCode,
    person_uuids: List[str],
):
    if listing_plan_code == PlanCode.UNLIMITED:
        raise ConflictException(detail="person.personHasAlreadyDownloaded")
    if len(person_uuids) > 10000:
        raise BadRequestException(detail="person.tooManyPersons")
    person_uuids_downloaded = (
        db.execute(
            sqlalchemy.select(TeamPerson.person_uuid)
            .where(col(TeamPerson.person_uuid).in_(person_uuids))
            .where(TeamPerson.team_id == current_user.team_id)
        )
        .scalars()
        .all()
    )

    person_uuids_will_download = [
        x for x in person_uuids if x not in person_uuids_downloaded
    ]

    amount_will_spend = settings.AMOUNT_PER_DOWNLOAD * len(person_uuids_will_download)

    if not is_enough_credit(
        db, current_user.team_id, amount_will_spend, ServiceCode.PERSON
    ):
        raise PaymentRequiredException(
            detail={
                "message": "person.notEnoughCredit",
                "remaining_credit": remaining_credit(
                    db, current_user.team_id, ServiceCode.PERSON
                ),
            }
        )

    try:
        team_persons = [
            TeamPerson(
                team_id=current_user.team_id,
                person_uuid=x,
            )
            for x in person_uuids_will_download
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
        # Consume credit
        consume_credit(
            db,
            current_user.team_id,
            amount_will_spend,
            service_code=ServiceCode.PERSON,
        )

        if len(person_uuids_will_download) > 0:
            ubq = UpdateByQuery(using=es_client, index=ESPersonExtend.Index.name)
            update_query = Q("terms", uuid=person_uuids_will_download)
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

    return person_uuids_will_download
