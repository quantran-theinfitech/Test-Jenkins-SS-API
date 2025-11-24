from json import dumps, loads

from sqlalchemy import text
from sqlmodel import Session, select

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    PaymentRequiredException,
)
from app.api.v1.schemas.person_collections import (
    AddPersonCollectionItemsRequest,
    CreatePersonCollectionRequest,
    TypeDownloadPerson,
)
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models import DownloadedHistory, PersonCollectionAssignee, TeamPerson
from app.models.person_collection import PersonCollection, StatusCode, TypeCode
from app.models.person_collection_item import PersonCollectionItem
from app.models.team import PlanCode
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit


def create_person_collections(
    request: CreatePersonCollectionRequest, db: Session, current_user: UserBase
):
    try:
        existing_collection = check_exist_collection_name(
            db, current_user.team_id, request.name
        )
        if existing_collection:
            raise BadRequestException(detail="common.duplicateName")

        search_condition = (
            SearchCrossRequest()
            if request.search_condition is None
            else request.search_condition
        )
        new_person_collection = PersonCollection(
            name=request.name,
            group_id=request.group_id,
            tags=request.tags,
            description=request.description,
            search_condition=loads(dumps(search_condition.dict(), default=str)),
            step=request.step,
            status_code=request.statusCode or StatusCode.Open,
            team_id=current_user.team_id,
            type_code=TypeCode.SYS,
        )
        db.add(new_person_collection)
        db.flush()
        db.refresh(new_person_collection)

        if request.main_person_id:
            person_collection_assignee = PersonCollectionAssignee(
                collection_id=new_person_collection.id,
                assignee_id=request.main_person_id,
            )
            db.add(person_collection_assignee)
            db.flush()

        db.commit()

        return new_person_collection.id
    except Exception as e:
        db.rollback()
        raise e


def save_person_collection_items(
    db: Session,
    request: AddPersonCollectionItemsRequest,
    current_user: UserBase,
    listing_plan_code: str,
):
    try:
        existing_names = []
        collection_ids = []
        unique_collection_names = list(set(request.collection_names))

        collection_names = """
            SELECT person_collections.id, person_collections.name
            FROM person_collections
            WHERE person_collections.team_id = :team_id
            AND person_collections.name = ANY(:collection_names)
            AND person_collections.deleted_at IS NULL
        """
        results = db.execute(
            text(collection_names),
            {
                "team_id": current_user.team_id,
                "collection_names": unique_collection_names,
            },
        ).all()
        if results:
            for result in results:
                existing_names.append(result.name)
                collection_ids.append(result.id)

            not_existing_names = list(
                set(unique_collection_names) - set(existing_names)
            )
        else:
            not_existing_names = unique_collection_names

        search_condition = (
            SearchCrossRequest()
            if request.search_condition is None
            else request.search_condition
        )
        for name in not_existing_names:
            new_person_collection = PersonCollection(
                name=name,
                search_condition=loads(dumps(search_condition.dict(), default=str)),
                status_code=StatusCode.Open,
                team_id=current_user.team_id,
                type_code=TypeCode.SYS,
            )
            db.add(new_person_collection)
            db.flush()
            db.refresh(new_person_collection)
            collection_ids.append(new_person_collection.id)

        if listing_plan_code is PlanCode.UNLIMITED:
            list_persons = request.uuids
        else:
            list_persons = get_list_person_download(
                db,
                current_user,
                request.type_download,
                request.uuids,
            )

        person_collection_items = [
            PersonCollectionItem(
                collection_id=collection_id,
                person_uuid=uuid,
            )
            for collection_id in collection_ids
            for uuid in list_persons
        ]
        db.bulk_save_objects(person_collection_items)
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    return collection_ids


def check_exist_collection_name(db: Session, team_id: int, name: str):
    collection = db.execute(
        select(PersonCollection).where(
            PersonCollection.team_id == team_id,
            PersonCollection.name == name,
            PersonCollection.deleted_at.is_(None),
        )
    ).first()
    return collection


def get_list_person_download(
    db: Session,
    current_user: UserBase,
    type_download: TypeDownloadPerson,
    list_person_uuids,
):
    uuids_downloaded = (
        db.execute(
            select(TeamPerson.person_uuid)
            .where(
                TeamPerson.team_id == current_user.team_id,
                TeamPerson.person_uuid.in_(list_person_uuids),
            )
            .distinct(TeamPerson.person_uuid)
        )
        .scalars()
        .all()
    )
    if type_download == TypeDownloadPerson.CREDIT.value:
        lock_person = [
            item for item in list_person_uuids if item not in uuids_downloaded
        ]
        amount_will_spend = settings.AMOUNT_PER_DOWNLOAD * len(lock_person)
        if not is_enough_credit(
            db,
            current_user.team_id,
            amount_will_spend,
            service_code=ServiceCode.PERSON,
        ):
            raise PaymentRequiredException(
                detail={
                    "message": "person.notEnoughCredit",
                    "remaining_credit": remaining_credit(
                        db, current_user.team_id, service_code=ServiceCode.PERSON
                    ),
                }
            )
        if len(lock_person) > 10000:
            raise ConflictException(detail="common.hasTooManyPersons")
        try:
            team_companies = [
                TeamPerson(
                    team_id=current_user.team_id,
                    person_uuid=x,
                )
                for x in lock_person
            ]
            db.bulk_save_objects(team_companies)
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
        except Exception as e:
            db.rollback()
            raise e
        return list_person_uuids

    return uuids_downloaded
