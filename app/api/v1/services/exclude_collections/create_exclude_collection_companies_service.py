import re
from datetime import datetime
from typing import List

from fastapi import UploadFile
from pandas import DataFrame, notnull, read_csv
from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.exclude_collections import (
    CompanyExcludeCollectionFieldName as FieldName,
)
from app.api.v1.schemas.exclude_collections import CreateCompanyExcludeCollectionRequest
from app.api.v1.schemas.users import UserBase
from app.db import engine
from app.models import CompanyExcludeCollection
from app.models.company_exclude_collection import StatusCode, TypeCode
from app.models.company_exclude_collection_item import CompanyExcludeCollectionItem
from utils.extract_domain import extract_domain


def read_exclude_collection_csv(file: UploadFile):
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
                FieldName.INFO.value: FieldName.INFO,
                FieldName.CORPORATE_NUMBER.value: "corporate_number",
                FieldName.TEL.value: "tel",
            },
            inplace=True,
        )

        if not notnull(df[FieldName.INFO]).all():
            raise BadRequestException(detail="uploadfile.incorrectFormat")

        # check if it is url or not
        regex = (
            r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\."
            + r"[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
        )

        urls = []
        names = []

        for row in df[FieldName.INFO]:
            domain = extract_domain(str(row))
            if re.match(regex, str(row)) and domain:
                urls.append(domain)
                names.append(None)
            else:
                names.append(row)
                urls.append(None)

        df.drop(columns=[FieldName.INFO], axis=1, inplace=True)
        df = df.assign(url=urls)
        df = df.assign(name=names)

        file.file.close()

        return df


def create_exclude_collection(
    db: Session,
    request: CreateCompanyExcludeCollectionRequest,
    current_user: UserBase,
    type_code: TypeCode,
):
    try:
        company_exclude_collections = CompanyExcludeCollection(
            team_id=current_user.team_id,
            name=request.name,
            description=request.description,
            type_code=type_code,
            status_code=StatusCode.PENDING,
            identification_rate=0,
            csv_path="",
        )
        db.add(company_exclude_collections)
        db.flush()
        db.refresh(company_exclude_collections)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return company_exclude_collections


def create_company_exclude_collection_items_by_csv(
    db: Session,
    company_exclude_collection: CompanyExcludeCollection,
    df: DataFrame,
    current_user: UserBase,
):
    exclude_companies_table_name = (
        f"exclude_temp_{current_user.team_id}"
        + f"_{current_user.id}_{datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S')}"
    )
    try:
        company_exclude_collection.status_code = StatusCode.PROCESSING
        db.add(company_exclude_collection)

        with engine.begin() as conn:
            df.to_sql(exclude_companies_table_name, con=conn, if_exists="fail")
            conn.commit()

        insert_query = f"""
            WITH cte AS (
            SELECT c.corporate_number as cn,
            ect.url as domain,
            ect.index as index,
            COUNT(ect.index) OVER (PARTITION BY ect.index) AS cnt
            FROM {exclude_companies_table_name} ect
            LEFT JOIN companies c
            ON (ect.corporate_number IS NOT NULL
                    AND ect.corporate_number = c.corporate_number)
                OR ( ect.corporate_number IS NULL
                        AND (
                            (ect.url IS NULL AND ect.name = c.name
                                AND ect.tel = c.phone)
                            OR (ect.name IS NULL AND ect.tel = c.phone
                                AND ect.url = c.domain)
                            OR (ect.tel IS NULL AND ect.url IS NULL
                                AND ect.name = c.name)
                            OR (ect.tel IS NULL AND ect.name IS NULL
                                AND ect.url = c.domain)
                        )
                )
            ),
            insert AS (
                INSERT INTO
                    company_exclude_collection_items(collection_id,corporate_number)
                SELECT {company_exclude_collection.id} , cn
                FROM cte WHERE (cnt = 1 OR domain IS NOT NULL) AND cn IS NOT NULL
                RETURNING corporate_number
            )
            SELECT COUNT (DISTINCT index)
            FROM cte WHERE cn IN (SELECT * FROM insert)
            """

        count = db.execute(text(insert_query)).scalar()
        identification_rate = count / len(df.index)

        company_exclude_collection.identification_rate = identification_rate
        company_exclude_collection.status_code = StatusCode.SUCCESS
        db.add(company_exclude_collection)

        db.commit()

    except Exception as e:
        # db rollback will rollback company_exclude_collections
        db.rollback()
        company_exclude_collection.status_code = StatusCode.ERROR
        db.add(company_exclude_collection)
        db.commit()
        raise e
    finally:
        drop_query = f"DROP TABLE IF EXISTS {exclude_companies_table_name}"
        db.execute(text(drop_query))
        # if there is no commit, the temporary table will not be deleted
        db.commit()


def create_exclude_collection_by_corporate_numbers(
    db: Session,
    corporate_numbers: List[str],
    company_exclude_collection: CompanyExcludeCollection,
):
    try:
        company_exclude_collection_items = [
            CompanyExcludeCollectionItem(
                corporate_number=corporate_number,
                collection_id=company_exclude_collection.id,
            )
            for corporate_number in corporate_numbers
        ]
        db.bulk_save_objects(company_exclude_collection_items)

        company_exclude_collection.status_code = StatusCode.SUCCESS
        db.add(company_exclude_collection)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return company_exclude_collection_items
