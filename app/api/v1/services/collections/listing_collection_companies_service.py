from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from .base_type_code import query_exclude_csv, type_code_is_csv_by_collection_id


def get_collection_companies(
    db: Session,
    collection_id: int,
    exclude_collection_id: Optional[int],
    team_id: Optional[int],
    keyword: Optional[str],
    per_page: int,
    page: int,
    order_by: str,
    order_by_desc_flag: bool,
    contact_form_url_flag: bool,
    contact_email_flag: bool,
):
    type_code_csv = type_code_is_csv_by_collection_id(db, collection_id)

    if type_code_csv:
        query_csv = f"""
                SELECT c.*
                {query_exclude_csv}
                LIMIT :limit OFFSET :offset
            """

        params = {
            "team_id": team_id,
            "target_collection_id": collection_id,
            "exclude_collection_id": exclude_collection_id,
            "limit": per_page,
            "offset": (page - 1) * per_page,
        }

        companies_custom = db.execute(
            text(query_csv),
            params,
        ).all()

        return companies_custom, type_code_csv
    else:
        keyword_query = ""
        order_by_query = "ORDER BY c.corporate_number"
        order_type_query = "ASC"
        contact_form_url_query = ""
        contact_email_query = ""
        exclude_collection_query = ""
        if keyword:
            keyword_query = """AND (c.name ILIKE :keyword OR c.kana_name
                ILIKE :keyword OR c.english_name ILIKE :keyword)"""
        if order_by:
            order_by_query = f"ORDER BY c.{order_by}"
        if order_by_desc_flag:
            order_type_query = "DESC"
        if contact_form_url_flag:
            contact_form_url_query = (
                "AND c.contact_form_url IS NOT NULL AND c.contact_form_url != ''"
            )

        if exclude_collection_id is not None:
            exclude_collection_query = (
                "AND cci.corporate_number NOT IN ("
                "    SELECT cci_sub.corporate_number "
                "    FROM company_collection_items cci_sub "
                "    WHERE cci_sub.collection_id = :exclude_collection_id)"
            )
        if contact_email_flag:
            contact_email_query = (
                "AND c.contact_email IS NOT NULL AND c.contact_email != ''"
            )
        query = f"""SELECT c.*, MAX(cc.team_id) AS team_id, MAX(tc.tags) AS tags,
                    MAX(tc."status_code") AS status_code,
                    COUNT(al.id) AS sales_log_count FROM company_collection_items cci
                    LEFT JOIN team_companies tc
                    ON tc.corporate_number = cci.corporate_number
                    LEFT JOIN companies c
                    ON cci.corporate_number = c.corporate_number
                    LEFT JOIN company_collections cc
                    ON cc.id = cci.collection_id
                    AND cc.team_id = tc.team_id
                    LEFT JOIN activity_logs al
                    ON al.corporate_number = tc.corporate_number
                    WHERE cc.id = :collection_id AND cc.team_id = :team_id
                    {keyword_query}
                    {exclude_collection_query}
                    {contact_form_url_query}
                    {contact_email_query}
                    GROUP BY c.id
                    {order_by_query}
                    {order_type_query}
                    LIMIT :limit OFFSET :offset
                """
        companies = db.execute(
            text(query),
            {
                "collection_id": collection_id,
                "exclude_collection_id": exclude_collection_id,
                "team_id": team_id,
                "keyword": f"%{keyword}%",
                "limit": per_page,
                "offset": (page - 1) * per_page,
                "order_by": order_by,
            },
        ).all()
        return companies, type_code_csv


def get_collection_companies_count(
    db: Session,
    collection_id: int,
    exclude_collection_id: int,
    team_id: Optional[int],
    keyword: Optional[str],
    contact_form_url_flag: bool,
    contact_email_flag: bool,
    type_code_csv: bool,
):
    if type_code_csv:
        query_csv = f"""
            SELECT COUNT(DISTINCT c.company_custom_id)
            {query_exclude_csv}
        """

        params = {
            "team_id": team_id,
            "target_collection_id": collection_id,
            "exclude_collection_id": exclude_collection_id,
        }

        result = db.execute(text(query_csv), params).scalar()

        return result or 0
    else:
        keyword_query = ""
        contact_form_url_query = ""
        contact_email_query = ""
        exclude_collection_query = ""
        if keyword:
            keyword_query = """AND (c.name LIKE :keyword OR c.kana_name
                LIKE :keyword OR c.english_name LIKE :keyword)"""
        if contact_form_url_flag:
            contact_form_url_query = (
                "AND c.contact_form_url IS NOT NULL AND c.contact_form_url != ''"
            )
        if contact_email_flag:
            contact_email_query = (
                "AND c.contact_email IS NOT NULL AND c.contact_email != ''"
            )
        if exclude_collection_id is not None:
            exclude_collection_query = (
                "AND cci.corporate_number NOT IN ("
                "    SELECT cci_sub.corporate_number "
                "    FROM company_collection_items cci_sub "
                "    WHERE cci_sub.collection_id = :exclude_collection_id)"
            )
        count_query = f"""SELECT COUNT(DISTINCT c.corporate_number)
                        FROM company_collection_items cci
                        LEFT JOIN companies c
                        ON c.corporate_number = cci.corporate_number
                        LEFT JOIN company_collections cc
                        ON cc.id = cci.collection_id
                        WHERE cc.team_id = :team_id AND cc.id = :collection_id
                        {keyword_query}
                        {exclude_collection_query}
                        {contact_form_url_query}
                        {contact_email_query}
                        """

        total = (
            db.execute(
                text(count_query),
                {
                    "collection_id": collection_id,
                    "exclude_collection_id": exclude_collection_id,
                    "team_id": team_id,
                    "keyword": f"%{keyword}%",
                },
            ).scalar()
            or 0
        )
        return total
