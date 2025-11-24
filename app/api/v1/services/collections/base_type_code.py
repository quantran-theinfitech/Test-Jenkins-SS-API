from sqlmodel import Session, text

query_exclude_csv = """
    FROM company_collections cc
    LEFT JOIN company_collection_items cci ON cc.id = cci.collection_id
    LEFT JOIN companies_custom c
        ON cci.company_custom_id = c.company_custom_id
    WHERE cc.team_id = :team_id
        AND c.contact_form_url IS NOT NULL
        AND cci.collection_id = :target_collection_id
        AND NOT EXISTS (
            SELECT 1
            FROM company_collection_items cci_exclude
            LEFT JOIN companies_custom c_exclude
                ON cci_exclude.company_custom_id
                    = c_exclude.company_custom_id
            WHERE cci_exclude.collection_id = :exclude_collection_id
                AND (
                    c_exclude.corporate_number = c.corporate_number
                    OR c_exclude.contact_form_url = c.contact_form_url
                )
        )
"""


def type_code_is_csv_by_collection_id(db: Session, collection_id: str) -> bool:
    check_exists_query = text(
        """
        SELECT 1
        FROM company_collections
        WHERE id = :collection_id
            AND type_code = 'CSV'
        LIMIT 1
        """
    )

    result = db.execute(
        check_exists_query, {"collection_id": collection_id}
    ).scalar_one_or_none()

    return result is not None


def type_code_is_csv_by_form_job_id(db: Session, form_job_id: str) -> bool:
    check_exists_query = text(
        """
        SELECT 1
        FROM form_jobs
        WHERE id = :form_job_id
            AND type_code = 'CSV'
        LIMIT 1
        """
    )

    result = db.execute(
        check_exists_query, {"form_job_id": form_job_id}
    ).scalar_one_or_none()

    return result is not None
