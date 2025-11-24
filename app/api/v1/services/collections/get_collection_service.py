from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.models.user import User

from .base_type_code import query_exclude_csv, type_code_is_csv_by_collection_id


def get_collection_detail(
    db: Session,
    collection_id: int,
    current_user: User,
    exclude_collection_id: Optional[str] = None,
    contact_form_url_flag: Optional[bool] = False,
    contact_email_flag: Optional[bool] = False,
):
    companies_count_query = ""
    join_companies = ""
    exclude_collection_query = ""

    type_code_csv = type_code_is_csv_by_collection_id(db, collection_id)
    is_exclude = exclude_collection_id is not None

    if type_code_csv:
        key_column = "company_custom_id"
        table_name = "companies_custom"
        if is_exclude:
            exclude_collection_query = f"""AND cci.{key_column} IN (
                SELECT c.{key_column}
                {query_exclude_csv}
            )"""
    else:
        key_column = "corporate_number"
        table_name = "companies"
        if is_exclude:
            exclude_collection_query = (
                f"AND cci.{key_column} NOT IN ("
                f"    SELECT cci_sub.{key_column} "
                f"    FROM company_collection_items cci_sub "
                f"    WHERE cci_sub.collection_id = :exclude_collection_id)"
            )

    if contact_form_url_flag and not contact_email_flag:
        condition = "c.contact_form_url IS NOT NULL AND c.contact_form_url != ''"
    elif not contact_form_url_flag and contact_email_flag:
        condition = "c.contact_email IS NOT NULL AND c.contact_email != ''"
    else:
        condition = f"cci.{key_column} IS NOT NULL {exclude_collection_query}"

    companies_count_query = (
        f"""
        COUNT(DISTINCT CASE WHEN {condition} THEN c.id END)"""
        if contact_form_url_flag or contact_email_flag
        else f"""
        COUNT(DISTINCT CASE WHEN {condition} THEN cci.{key_column} END)"""
    )

    join_companies = f"LEFT JOIN {table_name} c ON c.{key_column} = cci.{key_column}"

    query = text(
        f"""SELECT cc.*,
            COALESCE(
                ARRAY(
                    SELECT DISTINCT ON (cct.id)
                    jsonb_build_object('id', cct.id, 'name', cct.name)
                    FROM company_collection_tags cct
                    WHERE cct.collection_id = cc.id
                        AND cct.id IS NOT NULL AND cct.name IS NOT NULL
                ),
                ARRAY[]::jsonb[]
            ) AS tags,
            ({companies_count_query}) AS companies_count
            FROM company_collections cc
            LEFT JOIN company_collection_items cci ON cci.collection_id = cc.id
            {join_companies}
            WHERE cc.id = :target_collection_id
            AND cc.team_id = :team_id
            AND cc.deleted_at IS NULL
            GROUP BY cc.id"""
    )

    collection = db.execute(
        query,
        {
            "target_collection_id": collection_id,
            "team_id": current_user.team_id,
            "exclude_collection_id": exclude_collection_id,
        },
    ).first()

    if collection is None:
        raise ValueError("Collection not found")

    return collection
