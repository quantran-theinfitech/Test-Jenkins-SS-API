from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.schemas.collections import AddCollectionItemsByCSVRequest
from app.api.v1.schemas.users import UserBase
from app.models import CompanyCollection, CompanyCollectionItem, TeamCompany
from app.models.company_collection import ModeCode, StatusCode, TypeCode
from app.models.team_company import StatusCode as TeamCompanyStatusCode


def add_item_collection_by_csv_service(
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

        corporate_numbers, company_custom_ids = get_company_custom_ids(
            db, request.collection_id
        )
        company_collection_items = create_company_collection_items(
            db, collection_ids, corporate_numbers, company_custom_ids
        )
        team_companies = create_team_companies(db, current_user, company_custom_ids)

        db.bulk_save_objects(company_collection_items)
        db.bulk_save_objects(team_companies)
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
        SELECT company_collections.id, company_collections.name
        FROM company_collections
        WHERE company_collections.team_id = :team_id
        AND company_collections.name = ANY(:collection_names)
        AND company_collections.deleted_at IS NULL
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
        new_company_collection = CompanyCollection(
            team_id=current_user.team_id,
            name=name,
            status_code=StatusCode.Draft,
            type_code=TypeCode.CSV,
            group_id=1,
        )
        new_company_collection.mode_code = ModeCode.AUTO.value
        db.add(new_company_collection)
        db.flush()
        db.refresh(new_company_collection)
        collection_ids.append(new_company_collection.id)

    return collection_ids


def get_company_custom_ids(db, collection_id):
    company_custom_ids_query = """
        SELECT corporate_number, company_custom_id FROM company_collection_items
        WHERE collection_id = :collection_id
    """

    corporate_numbers = [
        row[0]
        for row in db.execute(
            text(company_custom_ids_query), {"collection_id": collection_id}
        ).all()
    ]

    company_custom_ids = [
        row[1]
        for row in db.execute(
            text(company_custom_ids_query), {"collection_id": collection_id}
        ).all()
    ]

    return corporate_numbers, company_custom_ids


def create_company_collection_items(
    db, collection_ids, corporate_numbers, company_custom_ids
):
    company_collection_items = []

    for collection_id in collection_ids:
        existing_corporate_numbers, existing_company_custom_ids = get_existing_items(
            db, collection_id
        )
        corporate_numbers, company_custom_ids = filter_existing_items(
            corporate_numbers,
            company_custom_ids,
            existing_corporate_numbers,
            existing_company_custom_ids,
        )
        company_collection_items.extend(
            create_items(collection_id, corporate_numbers, company_custom_ids)
        )

    return company_collection_items


def get_existing_items(db, collection_id):
    get_item_query = """
        SELECT corporate_number, company_custom_id FROM company_collection_items
        WHERE collection_id = :collection_id
    """

    existing_corporate_numbers = [
        row[0]
        for row in db.execute(
            text(get_item_query), {"collection_id": collection_id}
        ).all()
    ]

    existing_company_custom_ids = [
        row[1]
        for row in db.execute(
            text(get_item_query), {"collection_id": collection_id}
        ).all()
    ]

    return existing_corporate_numbers, existing_company_custom_ids


def filter_existing_items(
    corporate_numbers,
    company_custom_ids,
    existing_corporate_numbers,
    existing_company_custom_ids,
):
    matching_indexes = []

    existing_pairs = set(zip(existing_corporate_numbers, existing_company_custom_ids))

    for i, pair in enumerate(zip(corporate_numbers, company_custom_ids)):
        if pair in existing_pairs:
            matching_indexes.append(i)

    for i in sorted(matching_indexes, reverse=True):
        if 0 <= i < len(corporate_numbers):
            del corporate_numbers[i]
        if 0 <= i < len(company_custom_ids):
            del company_custom_ids[i]

    return corporate_numbers, company_custom_ids


def create_items(collection_id, corporate_numbers, company_custom_ids):
    return [
        CompanyCollectionItem(
            collection_id=collection_id,
            corporate_number=corporate_number,
            company_custom_id=company_custom_id,
        )
        for corporate_number, company_custom_id in zip(
            corporate_numbers, company_custom_ids
        )
    ]


def create_team_companies(db, current_user, company_custom_ids):
    get_exists_corporate_number_query = """
        SELECT corporate_number FROM team_companies
        WHERE team_id = :team_id
    """
    existing_corporate_numbers = [
        row[0]
        for row in db.execute(
            text(get_exists_corporate_number_query), {"team_id": current_user.team_id}
        ).all()
    ]
    return [
        TeamCompany(
            team_id=current_user.team_id,
            corporate_number=company_custom_id,
            status_code=TeamCompanyStatusCode.PENDING,
        )
        for company_custom_id in company_custom_ids
        if company_custom_id not in existing_corporate_numbers
    ]
