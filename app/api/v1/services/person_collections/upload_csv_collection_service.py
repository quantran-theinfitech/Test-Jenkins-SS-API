import uuid
from datetime import datetime

import pandas as pd
from fastapi import UploadFile
from pandas import DataFrame, read_csv
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Session

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.collections import CSVPersonCollectionFieldName as FieldName
from app.api.v1.schemas.users import UserBase
from app.constant.constants import DATE_FORMATS, ROLE_GROUP_CODE
from app.db import engine
from app.models import PersonCollection
from app.models.person_collection import StatusCode, TypeCode


def convert_to_datetime(date_str):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def convert_str_to_number(col):
    return (
        pd.to_numeric(col, errors="coerce")
        .where(pd.to_numeric(col, errors="coerce").notna(), None)
        .astype("object")
    )


def convert_str_to_list(series: pd.Series) -> pd.Series:
    return series.map(
        lambda x: (
            "{" + ",".join([s.strip() for s in str(x).split(",")]) + "}"
            if pd.notna(x) and str(x).strip()
            else None
        )
    )


def clean_and_split_list(col):
    return col.apply(lambda x: x.strip("{}").split(",") if isinstance(x, str) else [])


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

        columns_to_check = {"氏名", "name", "user_name"}

        if not (columns_to_check & set(df.columns)):
            error = "uploadfile.missingRequiredPersonName"
            file.file.close()
            raise BadRequestException(detail=error)

        for fieldname in df.columns.to_list():
            if (
                fieldname not in fieldnames
                and fieldname != "name"
                and fieldname != "user_name"
            ):
                error = "uploadfile.invalidTemplateError"
                file.file.close()
                raise BadRequestException(detail=error)

        df.rename(
            columns={field.value: field.name.lower() for field in FieldName},
            inplace=True,
        )

        df["role_group_codes"] = df["role_group_codes"].apply(
            lambda x: (
                "{"
                + ",".join(
                    [
                        next(
                            (k for k, v in ROLE_GROUP_CODE.items() if v == s.strip()),
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

        df["role_name"] = convert_str_to_list(df["role_name"])
        df["company_name"] = convert_str_to_list(df["company_name"])
        df["corporate_number"] = convert_str_to_list(df["corporate_number"])

        file.file.close()

        return df


def create_person_collection_when_uploading_csv(
    db: Session,
    name: str,
    current_user: UserBase,
):
    try:
        original_name = name.replace(".csv", "")
        counter = 1

        while (
            db.query(PersonCollection)
            .filter_by(name=name, team_id=current_user.team_id)
            .first()
        ):
            name = f"{original_name} ({counter}).csv"
            counter += 1

        person_collection = PersonCollection(
            name=name,
            team_id=current_user.team_id,
            group_id=1,
            status_code=StatusCode.Draft,
            type_code=TypeCode.CSV,
        )
        db.add(person_collection)
        db.flush()
        db.refresh(person_collection)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return person_collection


def create_person_collection_items_by_csv(
    db: Session,
    df: DataFrame,
    person_collection: PersonCollection,
    current_user: UserBase,
):
    person_table_name = (
        f"target_person_temp_{current_user.team_id}" + f"_{current_user.id}"
    )

    df["person_custom_uuid"] = [str(uuid.uuid4()) for _ in range(len(df))]

    while df["person_custom_uuid"].duplicated().any():
        df["person_custom_uuid"] = [str(uuid.uuid4()) for _ in range(len(df))]

    try:
        with engine.begin() as conn:
            df["role_group_codes"] = clean_and_split_list(df["role_group_codes"])
            df["corporate_number"] = clean_and_split_list(df["corporate_number"])
            df["role_name"] = clean_and_split_list(df["role_name"])
            df["company_name"] = clean_and_split_list(df["company_name"])

            df.to_sql(
                person_table_name,
                con=conn,
                if_exists="fail",
                dtype={
                    "role_group_codes": ARRAY(String),
                    "corporate_number": ARRAY(String),
                    "role_name": ARRAY(String),
                    "company_name": ARRAY(String),
                },
            )
            conn.commit()

        insert_query_items = f"""
            INSERT INTO person_collection_items(collection_id, person_custom_uuid)
            SELECT {person_collection.id}, person_custom_uuid
            FROM {person_table_name}
            WHERE person_custom_uuid IS NOT NULL
        """

        db.execute(text(insert_query_items))
        db.commit()

        columns_to_insert = list(df.columns)
        columns_str = ", ".join(columns_to_insert)

        insert_query_custom = f"""
            INSERT INTO persons_custom ({columns_str})
            SELECT {columns_str}
            FROM {person_table_name}
            WHERE person_custom_uuid IS NOT NULL
        """

        db.execute(text(insert_query_custom))
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    finally:
        drop_query = f"DROP TABLE IF EXISTS {person_table_name}"
        db.execute(text(drop_query))
        db.commit()
