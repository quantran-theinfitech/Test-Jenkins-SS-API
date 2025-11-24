import uuid
from datetime import datetime

import pandas as pd
from fastapi import UploadFile
from pandas import DataFrame, read_csv
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Session

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.collections import CSVCompanyCollectionFieldName as FieldName
from app.api.v1.schemas.users import UserBase
from app.constant.constants import (
    DATE_FORMATS,
    INDUSTRIES_CATEGORIES,
    LISTING_MARKET_CODE,
)
from app.db import engine
from app.models import CompanyCollection
from app.models.company_collection import ModeCode, StatusCode, TypeCode


def convert_to_datetime(date_str):
    if pd.isna(date_str) or date_str in [None, "", "NaT"]:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def convert_str_to_number(col):
    col = pd.to_numeric(col, errors="coerce")
    return col.astype("Int64")


def check_csv_collection_service(file: UploadFile):
    if file.content_type != "text/csv":
        error = "uploadfile.incorrectFormat"
        raise BadRequestException(detail=error)
    else:
        fieldnames = [fieldname.name.lower() for fieldname in FieldName] + [
            fieldname.value for fieldname in FieldName
        ]

        df = read_csv(file.file, keep_default_na=False)
        df = df.astype(str)
        df = df.replace("", None)

        columns_to_check = {"企業名", "name", "company_name"}

        if not (columns_to_check & set(df.columns)):
            error = "uploadfile.missingRequiredCompanyName"
            file.file.close()
            raise BadRequestException(detail=error)

        for fieldname in df.columns.to_list():
            if (
                fieldname not in fieldnames
                and fieldname != "name"
                and fieldname != "company_name"
            ):
                error = "uploadfile.invalidTemplateError"
                file.file.close()
                raise BadRequestException(detail=error)

        df.rename(
            columns={field.value: field.name.lower() for field in FieldName},
            inplace=True,
        )

        df["establish_at"] = df["establish_at"].apply(convert_to_datetime)
        df["establish_at"] = pd.to_datetime(df["establish_at"], errors="coerce")

        df["industry_code"] = df["industry_code"].apply(
            lambda x: next(
                (key for key, value in INDUSTRIES_CATEGORIES.items() if value == x), x
            )
        )

        df["listing_market_code"] = df["listing_market_code"].apply(
            lambda x: next(
                (key for key, value in LISTING_MARKET_CODE.items() if value == x), x
            )
        )

        df["sub_industries_code"] = df["sub_industries_code"].apply(
            lambda x: (
                "{"
                + ",".join(
                    [
                        next(
                            (
                                k
                                for k, v in INDUSTRIES_CATEGORIES.items()
                                if v["text"] == s.strip()
                            ),
                            s.strip(),
                        )
                        for s in str(x).split(",")
                        if s.strip()
                    ]
                )
                + "}"
                if isinstance(x, str) and x.strip()
                else None
            )
        )

        df["closing_month"] = convert_str_to_number(df["closing_month"])
        df["postal_code"] = convert_str_to_number(df["postal_code"])
        df["employees_count"] = convert_str_to_number(df["employees_count"])
        df["capital"] = convert_str_to_number(df["capital"])
        df["revenue"] = convert_str_to_number(df["revenue"])

        file.file.close()

        return df


def create_company_collection_when_uploading_csv(
    db: Session,
    name: str,
    current_user: UserBase,
):
    try:
        original_name = name.replace(".csv", "")
        counter = 1

        while (
            db.query(CompanyCollection)
            .filter_by(name=name, team_id=current_user.team_id)
            .first()
        ):
            name = f"{original_name} ({counter}).csv"
            counter += 1

        company_collection = CompanyCollection(
            name=name,
            team_id=current_user.team_id,
            group_id=1,
            status_code=StatusCode.Draft,
            type_code=TypeCode.CSV,
            mode_code=ModeCode.AUTO,
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

    df["company_custom_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    while df["company_custom_id"].duplicated().any():
        df["company_custom_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    try:
        with engine.begin() as conn:
            df["sub_industries_code"] = df["sub_industries_code"].apply(
                lambda x: x.strip("{}").split(",") if isinstance(x, str) else []
            )

            df.to_sql(
                companies_table_name,
                con=conn,
                if_exists="fail",
                dtype={"sub_industries_code": ARRAY(String)},
            )
            conn.commit()

        insert_query_items = f"""
            INSERT INTO company_collection_items(collection_id, company_custom_id)
            SELECT {company_collection.id}, company_custom_id
            FROM {companies_table_name}
            WHERE company_custom_id IS NOT NULL
        """

        db.execute(text(insert_query_items))
        db.commit()

        columns_to_insert = [col for col in df.columns if col != "revenue_predict"]
        columns_str = ", ".join(columns_to_insert)

        insert_query_custom = f"""
            INSERT INTO companies_custom ({columns_str})
            SELECT {columns_str}
            FROM {companies_table_name}
            WHERE company_custom_id IS NOT NULL
        """

        db.execute(text(insert_query_custom))
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    finally:
        drop_query = f"DROP TABLE IF EXISTS {companies_table_name}"
        db.execute(text(drop_query))
        db.commit()
