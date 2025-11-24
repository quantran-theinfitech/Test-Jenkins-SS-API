# flake8: noqa: E501
import re
from json import dumps, loads

from elasticsearch_dsl import Q
from fastapi import UploadFile
from pandas import DataFrame, read_csv
from sqlalchemy import text
from sqlmodel import Session, select

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    PaymentRequiredException,
)
from app.api.v1.queries.company import build_es_query
from app.api.v1.schemas.collections import AddCollectionItemsRequest
from app.api.v1.schemas.collections import CompanyCollectionFieldName as FieldName
from app.api.v1.schemas.collections import CreateCollectionRequest, TypeDownloadCompany
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.db import engine
from app.models import (
    CompanyCollection,
    CompanyCollectionAssignee,
    CompanyCollectionItem,
    CompanyCollectionTag,
    DownloadedHistory,
    TeamCompany,
)
from app.models.company_collection import ModeCode, StatusCode, TypeCode
from app.models.team import PlanCode
from app.models.team_company import StatusCode as TeamCompanyStatusCode
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit


def create_collection(
    db: Session,
    request: CreateCollectionRequest,
    current_user: UserBase,
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
        new_company_collection = CompanyCollection(
            team_id=current_user.team_id,
            name=request.name,
            group_id=request.group_id,
            status_code=request.statusCode or StatusCode.Open,
            description=request.description,
            step=request.step,
            search_condition=loads(dumps(search_condition.dict(), default=str)),
        )
        new_company_collection.mode_code = ModeCode(request.mode.value)
        db.add(new_company_collection)
        db.flush()
        db.refresh(new_company_collection)

        if request.main_person_id:
            company_collection_assignee = CompanyCollectionAssignee(
                collection_id=new_company_collection.id,
                user_id=request.main_person_id,
            )
            db.add(company_collection_assignee)
            db.flush()

        company_collection_tags = [
            CompanyCollectionTag(collection_id=new_company_collection.id, name=tag)
            for tag in request.tags
        ]
        db.bulk_save_objects(company_collection_tags)
        db.flush()
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return new_company_collection.id


def save_collection_items(
    db: Session,
    request: AddCollectionItemsRequest,
    current_user: UserBase,
    listing_plan_code: str,
):
    try:
        existing_names = []
        collection_ids = []
        unique_collection_names = list(set(request.collection_names))

        collection_names = """
            SELECT company_collections.id, company_collections.name
            FROM company_collections
            WHERE company_collections.team_id = :team_id
            AND company_collections.name = ANY(:collection_names)
            AND company_collections.deleted_at IS NULL
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
            new_company_collection = CompanyCollection(
                team_id=current_user.team_id,
                name=name,
                status_code=StatusCode.Open,
                search_condition=loads(dumps(search_condition.dict(), default=str)),
            )
            new_company_collection.mode_code = ModeCode.MANUAL.value
            db.add(new_company_collection)
            db.flush()
            db.refresh(new_company_collection)
            collection_ids.append(new_company_collection.id)

        if listing_plan_code is PlanCode.UNLIMITED:
            corporate_numbers_downloaded = request.corporate_numbers
        else:
            corporate_numbers_downloaded = get_list_company_download(
                db,
                current_user,
                request.type_download,
                request.corporate_numbers,
            )

        # Lấy các cặp (collection_id, corporate_number) đã tồn tại
        existing_items = (
            db.query(CompanyCollectionItem)
            .filter(
                CompanyCollectionItem.collection_id.in_(collection_ids),
                CompanyCollectionItem.corporate_number.in_(
                    corporate_numbers_downloaded
                ),
            )
            .all()
        )
        existing_pairs = {
            (item.collection_id, item.corporate_number) for item in existing_items
        }

        # Chỉ insert những cặp chưa tồn tại
        company_collection_items = [
            CompanyCollectionItem(
                collection_id=collection_id,
                corporate_number=corporate_number,
            )
            for collection_id in collection_ids
            for corporate_number in corporate_numbers_downloaded
            if (collection_id, corporate_number) not in existing_pairs
        ]
        if company_collection_items:
            db.bulk_save_objects(company_collection_items)
        db.flush()
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return collection_ids


def insert_collection_items_from_es(
    db: Session,
    listing_plan_code: PlanCode,
    team_id: int,
    search_condition: SearchCrossRequest,
    new_company_collection_id,
    es_client,
):
    search = EsCompanyExtend.search(using=es_client, index=EsCompanyExtend.Index.name)
    search = search.source(["corporate_number"])

    search_query = build_es_query(search_condition)
    if listing_plan_code is not PlanCode.UNLIMITED:
        queries = []
        queries.append(search_query)
        queries.append(Q("term", team_ids=team_id))
        collection_item_query = Q("bool", must=queries)
    else:
        collection_item_query = search_query

    search = search.query(collection_item_query)
    pagination_param = {"size": 0, "track_total_hits": True}
    result = search.extra(**pagination_param).execute()["hits"]
    total = result._d_["total"]["value"]
    if total > 10000:
        raise BadRequestException(detail="common.hasTooManyCompanies")

    pagination_param = {"size": total, "track_total_hits": True}
    result = search.extra(**pagination_param).execute()["hits"]
    data = result["hits"]._l_

    corporate_numbers = [x["_source"]["corporate_number"] for x in data]
    company_collection_items = [
        CompanyCollectionItem(
            collection_id=new_company_collection_id,
            corporate_number=corporate_number,
        )
        for corporate_number in corporate_numbers
    ]
    if listing_plan_code is PlanCode.UNLIMITED:
        team_companies = [
            TeamCompany(
                team_id=team_id,
                corporate_number=corporate_number,
                status_code=TeamCompanyStatusCode.PENDING,
            )
            for corporate_number in corporate_numbers
        ]
        db.bulk_save_objects(team_companies)
    db.bulk_save_objects(company_collection_items)
    db.flush()


def read_collection_csv(file: UploadFile):
    if file.content_type != "text/csv":
        raise BadRequestException(detail="uploadfile.incorrectFormat")
    else:
        fieldnames = [fieldname.value for fieldname in FieldName]
        df = read_csv(file.file, keep_default_na=False)
        df = df.astype(str)
        df = df.replace("", None)

        for fieldname in df.columns.to_list():
            if fieldname not in fieldnames:
                raise BadRequestException(detail="uploadfile.incorrectFormat")

        df.rename(
            columns={
                FieldName.COMPANY_NAME.value: "company_name",
                FieldName.FORM_URL.value: "form_url",
            },
            inplace=True,
        )

        # check if it is url or not
        regex = (
            r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\."
            + r"[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
        )

        for row in df["form_url"]:
            if re.match(regex, str(row)) is None:
                raise BadRequestException(detail="uploadfile.incorrectURLFormat")

        file.file.close()

        return df


def create_company_collection_when_uploading_csv(
    db: Session,
    request: CreateCollectionRequest,
    current_user: UserBase,
):
    try:
        company_collection = CompanyCollection(
            name=request.name,
            team_id=current_user.team_id,
            group_id=1,  # default group ID
            status_code=StatusCode.Draft,
            type_code=TypeCode.CSV,
        )
        db.add(company_collection)
        db.flush()
        db.refresh(company_collection)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return company_collection


def create_company_collection_items_by_csv(
    db: Session,
    df: DataFrame,
    company_collection: CompanyCollection,
    current_user: UserBase,
):
    companies_table_name = (
        f"target_companies_temp_{current_user.team_id}" + f"_{current_user.id}"
    )
    try:
        with engine.begin() as conn:
            df.to_sql(companies_table_name, con=conn, if_exists="fail")
            conn.commit()

        insert_query = f"""
            WITH cte AS (
            SELECT c.corporate_number as cn, ct.index as index
            FROM {companies_table_name} ct
            LEFT JOIN companies c
            ON (ct.company_name = c.name OR ct.form_url = c.contact_form_url)
            )
            INSERT INTO company_collection_items(collection_id,corporate_number)
            SELECT {company_collection.id} , cn
            FROM cte WHERE cn IS NOT NULL
            """
        db.execute(text(insert_query))
        db.commit()

    except Exception as e:
        db.rollback()
        raise e
    finally:
        drop_query = f"DROP TABLE IF EXISTS {companies_table_name}"
        db.execute(text(drop_query))
        db.commit()


def check_exist_collection_name(db: Session, team_id: int, name: str):
    collection = db.execute(
        select(CompanyCollection).where(
            CompanyCollection.team_id == team_id,
            CompanyCollection.name == name,
            CompanyCollection.deleted_at.is_(None),
        )
    ).first()
    return collection


def get_list_company_download(
    db: Session,
    current_user: UserBase,
    type_download: TypeDownloadCompany,
    list_corporate_numbers,
):
    corporate_numbers_downloaded = (
        db.execute(
            select(TeamCompany.corporate_number)
            .where(
                TeamCompany.team_id == current_user.team_id,
                TeamCompany.corporate_number.in_(list_corporate_numbers),
            )
            .distinct(TeamCompany.corporate_number)
        )
        .scalars()
        .all()
    )
    if type_download == TypeDownloadCompany.CREDIT.value:
        lock_company = [
            item
            for item in list_corporate_numbers
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
                    status_code=TeamCompanyStatusCode.PENDING,
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
        except Exception as e:
            db.rollback()
            raise e
        return list_corporate_numbers

    return corporate_numbers_downloaded
