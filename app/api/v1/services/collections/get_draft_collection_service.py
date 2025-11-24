from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.models.user import User


def get_draft_collection_detail(
    db: Session,
    collection_id: int,
    current_user: User,
    contact_form_url_flag: Optional[bool] = False,
):
    companies_count = ""
    join_companies = ""
    if contact_form_url_flag is True:
        companies_count = """COUNT(DISTINCT CASE WHEN c.contact_form_url IS NOT NULL
        AND c.contact_form_url != '' THEN c.id ELSE NULL END) AS companies_count"""
        join_companies = (
            "LEFT JOIN companies c ON c.corporate_number = cci.corporate_number"
        )
    else:
        companies_count = "COUNT(DISTINCT cci.corporate_number)  AS companies_count"

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
            ARRAY_AGG(DISTINCT cci.corporate_number) FILTER
            (WHERE cci.corporate_number IS NOT NULL)
            AS corporate_numbers,
            MAX(cca.user_id) AS main_person_id,
            {companies_count}
            FROM company_collections cc
            LEFT JOIN company_collection_items cci ON cci.collection_id = cc.id
            LEFT JOIN
                company_collection_assignees cca ON cc.id = cca.collection_id
            {join_companies}
            WHERE cc.id = :collection_id
            AND cc.team_id = :team_id
            AND cc.deleted_at IS NULL
            GROUP BY cc.id"""
    )
    collection = db.execute(
        query, {"collection_id": collection_id, "team_id": current_user.team_id}
    ).first()
    return collection
