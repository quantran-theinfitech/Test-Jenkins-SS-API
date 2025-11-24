from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.schemas.collections import AddCollectionItemsByCSVRequest
from app.api.v1.schemas.users import UserBase
from app.models import PersonCollection, PersonCollectionItem, TeamPerson
from app.models.person_collection import StatusCode, TypeCode


def add_person_item_collection_by_csv_service(
    db: Session,
    request: AddCollectionItemsByCSVRequest,
    current_user: UserBase,
):
    try:
        unique_collection_names = list(set(request.collection_names))
        existing_names, collection_ids = get_existing_collections(
            db, current_user, unique_collection_names
        )
        not_existing_names = list(set(unique_collection_names) - set(existing_names))

        collection_ids.extend(
            create_new_collections(db, current_user, not_existing_names)
        )

        person_uuids, person_custom_uuids = get_person_custom_uuids(
            db, request.collection_id
        )
        person_collection_items = create_person_collection_items(
            db, collection_ids, person_uuids, person_custom_uuids
        )
        team_person = create_team_person(db, current_user, person_custom_uuids)

        db.bulk_save_objects(person_collection_items)
        db.bulk_save_objects(team_person)
        db.flush()
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return collection_ids


def get_existing_collections(db, current_user, unique_collection_names):
    existing_names = []
    collection_ids = []

    collection_names_query = """
        SELECT person_collections.id, person_collections.name
        FROM person_collections
        WHERE person_collections.team_id = :team_id
        AND person_collections.name = ANY(:collection_names)
        AND person_collections.deleted_at IS NULL
    """

    results = db.execute(
        text(collection_names_query),
        {
            "team_id": current_user.team_id,
            "collection_names": unique_collection_names,
        },
    ).all()

    if results:
        for result in results:
            existing_names.append(result.name)
            collection_ids.append(result.id)

    return existing_names, collection_ids


def create_new_collections(db, current_user, not_existing_names):
    collection_ids = []

    for name in not_existing_names:
        new_person_collection = PersonCollection(
            team_id=current_user.team_id,
            name=name,
            status_code=StatusCode.Draft,
            type_code=TypeCode.CSV,
            group_id=1,
        )
        db.add(new_person_collection)
        db.flush()
        db.refresh(new_person_collection)
        collection_ids.append(new_person_collection.id)

    return collection_ids


def get_person_custom_uuids(db, collection_id):
    person_custom_uuids_query = """
        SELECT person_uuid, person_custom_uuid FROM person_collection_items
        WHERE collection_id = :collection_id
    """

    person_uuids = [
        row[0]
        for row in db.execute(
            text(person_custom_uuids_query), {"collection_id": collection_id}
        ).all()
    ]

    person_custom_uuids = [
        row[1]
        for row in db.execute(
            text(person_custom_uuids_query), {"collection_id": collection_id}
        ).all()
    ]

    return person_uuids, person_custom_uuids


def create_person_collection_items(
    db, collection_ids, person_uuids, person_custom_uuids
):
    person_collection_items = []

    for collection_id in collection_ids:
        existing_person_uuids, existing_person_custom_uuids = get_existing_items(
            db, collection_id
        )
        person_uuids, person_custom_uuids = filter_existing_items(
            person_uuids,
            person_custom_uuids,
            existing_person_uuids,
            existing_person_custom_uuids,
        )
        person_collection_items.extend(
            create_items(collection_id, person_uuids, person_custom_uuids)
        )

    return person_collection_items


def get_existing_items(db, collection_id):
    get_item_query = """
        SELECT person_uuid, person_custom_uuid FROM person_collection_items
        WHERE collection_id = :collection_id
    """

    existing_person_uuids = [
        row[0]
        for row in db.execute(
            text(get_item_query), {"collection_id": collection_id}
        ).all()
    ]

    existing_person_custom_uuids = [
        row[1]
        for row in db.execute(
            text(get_item_query), {"collection_id": collection_id}
        ).all()
    ]

    return existing_person_uuids, existing_person_custom_uuids


def filter_existing_items(
    person_uuids,
    person_custom_uuids,
    existing_person_uuids,
    existing_person_custom_uuids,
):
    matching_indexes = []

    existing_pairs = set(zip(existing_person_uuids, existing_person_custom_uuids))

    for i, pair in enumerate(zip(person_uuids, person_custom_uuids)):
        if pair in existing_pairs:
            matching_indexes.append(i)

    for i in sorted(matching_indexes, reverse=True):
        if 0 <= i < len(person_uuids):
            del person_uuids[i]
        if 0 <= i < len(person_custom_uuids):
            del person_custom_uuids[i]

    return person_uuids, person_custom_uuids


def create_items(collection_id, person_uuids, person_custom_uuids):
    return [
        PersonCollectionItem(
            collection_id=collection_id,
            person_uuid=person_uuid,
            person_custom_uuid=person_custom_uuid,
        )
        for person_uuid, person_custom_uuid in zip(person_uuids, person_custom_uuids)
    ]


def create_team_person(db, current_user, person_custom_uuids):
    get_exists_person_uuid_query = """
        SELECT person_uuid FROM team_persons
        WHERE team_id = :team_id
    """
    existing_person_uuids = [
        row[0]
        for row in db.execute(
            text(get_exists_person_uuid_query), {"team_id": current_user.team_id}
        ).all()
    ]

    return [
        TeamPerson(
            team_id=current_user.team_id,
            person_uuid=person_custom_uuid,
        )
        for person_custom_uuid in person_custom_uuids
        if person_custom_uuid not in existing_person_uuids
    ]
