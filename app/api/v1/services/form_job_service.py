# flake8: noqa: E501
import i18n
from sqlalchemy import select, text
from sqlmodel import Session

from app.api.base.exceptions import NotFoundException, PaymentRequiredException
from app.api.v1.schemas.form_jobs import CreateFormJobRequest, FormJobDetailResponse
from app.api.v1.schemas.placeholders import Placeholder
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models.form_job import FormJob, FormJobStatusCode
from app.models.form_job import FormJobTypeCode as TypeCode
from app.models.form_job_item import FormJobItemStatusCode
from app.models.form_template import FormTemplate
from app.models.placeholder import PlaceHolder
from app.models.placeholder_item import PlaceHolderItem
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit

from .collections.base_type_code import (
    query_exclude_csv,
    type_code_is_csv_by_collection_id,
    type_code_is_csv_by_form_job_id,
)


class FormJobService:
    def __init__(self, db: Session):
        self.db = db

    def count_company_collection_items(
        self,
        request: CreateFormJobRequest,
        current_user: UserBase,
    ):
        type_code_csv = type_code_is_csv_by_collection_id(
            self.db, request.target_collection_id
        )

        if type_code_csv:
            count_query = text(
                f"""
                SELECT COUNT(cci.id)
                {query_exclude_csv}
            """
            )

            params = {
                "team_id": current_user.team_id,
                "target_collection_id": request.target_collection_id,
                "exclude_collection_id": request.exclude_collection_id,
            }

            total_company_collection_items = (
                self.db.execute(count_query, params).scalar_one_or_none() or 0
            )

            return total_company_collection_items, TypeCode.CSV

        else:
            count_query = text(
                """
                SELECT COUNT(cci.id)
                FROM company_collections cc
                LEFT JOIN company_collection_items cci ON cc.id = cci.collection_id
                LEFT JOIN companies c ON cci.corporate_number = c.corporate_number
                WHERE cc.team_id = :team_id
                    AND cci.collection_id = :target_collection_id
                    AND NOT EXISTS (
                        SELECT 1
                        FROM company_collection_items cci_exclude
                        WHERE cci_exclude.collection_id = :exclude_collection_id
                            AND cci_exclude.corporate_number = cci.corporate_number
                    )
            """
            )

            params = {
                "team_id": current_user.team_id,
                "target_collection_id": request.target_collection_id,
                "exclude_collection_id": request.exclude_collection_id,
            }

            total_company_collection_items = (
                self.db.execute(count_query, params).scalar_one_or_none() or 0
            )

            return total_company_collection_items, TypeCode.SYS

    def create_form_job(
        self,
        total_company_collection_items: int,
        request: CreateFormJobRequest,
        current_user: UserBase,
        type_code: TypeCode,
    ):
        if total_company_collection_items == 0:
            raise NotFoundException("company.companyNotFound")

        amount_will_spend = (
            total_company_collection_items * settings.AMOUNT_PER_JOB_ITEM
        )

        if not is_enough_credit(
            self.db, current_user.team_id, amount_will_spend, ServiceCode.CTF
        ):
            raise PaymentRequiredException("company.notEnoughCredit")

        total_remaining_credit = remaining_credit(
            self.db, current_user.team_id, ServiceCode.CTF
        )
        total = int(total_remaining_credit / settings.AMOUNT_PER_JOB_ITEM)
        total = total if total > 0 else 0
        total_company_collection_items = (
            total
            if total_company_collection_items > total
            else total_company_collection_items
        )

        if total_company_collection_items <= 0:
            raise PaymentRequiredException("company.notEnoughCredit")

        try:
            form_job = FormJob(
                team_id=current_user.team_id,
                template_id=request.template_id,
                placeholder_id=request.placeholder_id,
                target_collection_id=request.target_collection_id,
                exclude_collection_id=request.exclude_collection_id,
                approach_ng_flag=request.approach_ng_flag,
                schedule_at=request.schedule_at,
                status_code=FormJobStatusCode.PENDING,
                type_code=type_code,
                form_schedule_id=request.form_schedule_id,
            )

            self.db.add(form_job)
            self.db.flush()
            self.db.refresh(form_job)

            consume_credit(
                self.db,
                current_user.team_id,
                amount_will_spend,
                service_code=ServiceCode.CTF,
            )

        except Exception as e:
            self.db.rollback()
            raise e

        return form_job.id, total_company_collection_items

    def create_form_job_items(
        self,
        form_job_id: int,
        total_company_collection_items: int,
        request: CreateFormJobRequest,
        current_user: UserBase,
        type_code: TypeCode,
    ):
        try:
            if type_code is TypeCode.SYS:
                insert_into = text(
                    """
                    INSERT INTO form_job_items
                        (corporate_number, form_url, job_id, status_code)
                    SELECT c.corporate_number, c.contact_form_url,
                        :form_job_id as job_id,
                        :status_code as status_code
                    FROM company_collections cc
                    LEFT JOIN company_collection_items cci
                        ON cc.id = cci.collection_id
                    LEFT JOIN companies c
                        ON cci.corporate_number = c.corporate_number
                    WHERE cc.team_id = :team_id
                        AND cci.collection_id = :target_collection_id
                        AND NOT EXISTS (
                            SELECT 1
                            FROM company_collection_items cci_exclude
                            WHERE cci_exclude.collection_id = :exclude_collection_id
                                AND cci_exclude.corporate_number = cci.corporate_number
                        )
                    LIMIT :total_company_collection_items
                    """
                )
            else:
                insert_into = text(
                    f"""
                    INSERT INTO form_job_items
                        (company_custom_id, form_url, job_id, status_code)
                    SELECT c.company_custom_id, c.contact_form_url,
                        :form_job_id as job_id,
                        :status_code as status_code
                    {query_exclude_csv}
                    LIMIT :total_company_collection_items
                    """
                )

            params = {
                "form_job_id": form_job_id,
                "status_code": FormJobItemStatusCode.PENDING.name,
                "team_id": current_user.team_id,
                "target_collection_id": request.target_collection_id,
                "exclude_collection_id": request.exclude_collection_id,
                "total_company_collection_items": total_company_collection_items,
            }

            self.db.execute(insert_into, params)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise e

    def listing_form_jobs(
        self, current_user: UserBase, page: int, per_page: int, keyword: str
    ):

        query_keyword = ""
        if keyword:
            query_keyword = """ AND cc.name ILIKE :keyword"""

        query = f"""
        SELECT fj.*,
        max(p.name) AS placeholder_name,
        max(ft.title) AS template_title,
        max(cec.name) AS exclude_collection_name,
        max(cc.name) AS target_collection_name,
        CASE
            WHEN (SELECT COUNT(fji_sub.company_custom_id)
                FROM form_job_items fji_sub
                WHERE fji_sub.job_id = fj.id) > 0
            THEN (SELECT COUNT(fji_sub.company_custom_id)
                FROM form_job_items fji_sub
                WHERE fji_sub.job_id = fj.id)

            WHEN (SELECT COUNT(fji_sub.corporate_number)
                FROM form_job_items fji_sub
                WHERE fji_sub.job_id = fj.id) > 0
            THEN (SELECT COUNT(fji_sub.corporate_number)
                FROM form_job_items fji_sub
                WHERE fji_sub.job_id = fj.id)

            ELSE 0
        END AS collection_item_count,
        COUNT(fji2.id) FILTER (WHERE fji2.status_code = 'SUCCESS') AS success_count,
        (SELECT CASE
            WHEN COUNT(fji.id) = 0 THEN 0
            ELSE COUNT(fji.id)
            FILTER (WHERE fji.status_code = 'SUCCESS')::float / COUNT(fji.id)
            END
        FROM form_job_items fji
        WHERE fji.job_id = fj.id) AS success_rate,
        CASE WHEN fj.status_code in ('RUNNING', 'PENDING')
            THEN case
                WHEN sum(CASE WHEN fji2.status_code = 'PENDING' THEN 1 ELSE 0 END) > 0
                    AND
                    sum(CASE WHEN fji2.status_code = 'RUNNING' THEN 1 ELSE 0 END) = 0
                    AND
                    sum(CASE WHEN fji2.status_code = 'QUEUED' THEN 1 ELSE 0 END) = 0
                    THEN 'PENDING'::public.form_job_status_code
                WHEN sum(CASE WHEN fji2.status_code = 'RUNNING' THEN 1 ELSE 0 END) > 0
                    OR
                    sum(CASE WHEN fji2.status_code = 'QUEUED' THEN 1 ELSE 0 END) > 0
                    THEN 'RUNNING'::public.form_job_status_code
                WHEN sum(CASE WHEN fji2.status_code = 'PENDING' THEN 1 ELSE 0 END) = 0
                    AND
                    sum(CASE WHEN fji2.status_code = 'RUNNING' THEN 1 ELSE 0 END) = 0
                    AND
                    sum(CASE WHEN fji2.status_code = 'QUEUED' THEN 1 ELSE 0 END) = 0
                    THEN 'DONE'::public.form_job_status_code
                END
            ELSE fj.status_code
        END AS status_code_item_sum
        FROM form_jobs fj
        LEFT JOIN placeholders p ON p.id = fj.placeholder_id
        LEFT JOIN form_templates ft ON ft.id = fj.template_id
        LEFT JOIN company_collections cec ON cec.id = fj.exclude_collection_id
        LEFT JOIN company_collections cc ON cc.id = fj.target_collection_id
        LEFT JOIN form_job_items fji2 ON fj.id = fji2.job_id
        WHERE fj.team_id = :team_id
        {query_keyword}
        GROUP BY fj.id
        ORDER BY fj.created_at DESC
        LIMIT :limit OFFSET :offset
        """
        form_jobs = self.db.execute(
            text(query),
            {
                "team_id": current_user.team_id,
                "limit": per_page,
                "offset": (page - 1) * per_page,
                "keyword": f"%{keyword}%",
            },
        ).all()
        return form_jobs

    def listing_form_jobs_count(self, current_user: UserBase, keyword: str):
        query_keyword = ""
        if keyword:
            query_keyword = """ AND cc.name ILIKE :keyword"""

        query_total = f"""SELECT
                    count(fj.*)
                    FROM
                    form_jobs fj
                    LEFT JOIN company_collections cc ON cc.id = fj.target_collection_id
                    WHERE
                    fj.team_id = :team_id
                    {query_keyword}
                    """
        total = (
            self.db.execute(
                text(query_total),
                {
                    "team_id": current_user.team_id,
                    "keyword": f"%{keyword}%",
                },
            ).scalar()
            or 0
        )
        return total

    def listing_form_job_items(self, job_id, page: int, per_page: int, team_id: int):
        type_code_is_csv = type_code_is_csv_by_form_job_id(self.db, job_id)
        key_column, table_name = (
            ("company_custom_id", "companies_custom")
            if type_code_is_csv
            else ("corporate_number", "companies")
        )

        query = f"""
            SELECT c.*,
                fji.company_custom_id,
                fji.status_code,
                fji.form_url,
                fji.started_at,
                fji.ended_at,
                MAX(tc.tags) AS tags
            FROM form_job_items fji
            LEFT JOIN {table_name} c
                ON c.{key_column} = fji.{key_column}
            LEFT JOIN team_companies tc
                ON tc.corporate_number = c.{key_column}
            WHERE fji.job_id = :job_id
            AND tc.team_id = :team_id
            GROUP BY fji.id, c.id, c.name, c.address
            ORDER BY fji.created_at DESC
            LIMIT :limit OFFSET :offset
        """

        form_job_items = self.db.execute(
            text(query),
            {
                "job_id": job_id,
                "team_id": team_id,
                "limit": per_page,
                "offset": (page - 1) * per_page,
            },
        ).all()
        return form_job_items

    def get_tags_description(self, job_id, current_user: UserBase):
        form_job = (
            self.db.query(FormJob)
            .filter(FormJob.id == job_id, FormJob.team_id == current_user.team_id)
            .first()
        )
        if not form_job:
            raise NotFoundException(i18n.t("common.notFound"))

        query = """SELECT
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
                    cc.description AS description,
                    cc.name AS job_name
                    FROM form_job_items fji
                    LEFT JOIN form_jobs fj
                    ON fj.id = :job_id
                    LEFT JOIN company_collections cc
                    ON cc.id = fj.target_collection_id
                    WHERE fji.job_id = :job_id
                    """

        result = self.db.execute(
            text(query),
            {
                "job_id": job_id,
            },
        ).first()

        if not result:
            return [], None, None

        tags, description, job_name = result
        return tags, description, job_name

    def listing_form_job_items_count(self, job_id):
        query_total = """SELECT COUNT(fji.*)
                         FROM form_job_items fji
                         WHERE fji.job_id = :job_id"""
        total = (
            self.db.execute(
                text(query_total),
                {
                    "job_id": job_id,
                },
            ).scalar()
            or 0
        )
        query_contact_form_url_count = """SELECT COUNT(fji.*)
                         FROM form_job_items fji
                         WHERE fji.job_id = :job_id
                         AND fji.form_url IS NOT NULL
                         """
        contact_form_url_count = (
            self.db.execute(
                text(query_contact_form_url_count),
                {
                    "job_id": job_id,
                },
            ).scalar()
            or 0
        )

        return total, contact_form_url_count

    def get_form_job_detail(
        self, form_id: int, current_user: UserBase
    ) -> FormJobDetailResponse:
        form_job = self.db.query(FormJob).filter(FormJob.id == form_id).first()
        if not form_job:
            raise NotFoundException(i18n.t("common.notFound"))

        placeholder_id = form_job.placeholder_id
        template_id = form_job.template_id

        placeholder_data = self.db.exec(
            select(
                PlaceHolder.name, PlaceHolderItem.attr_name, PlaceHolderItem.attr_value
            )
            .join(PlaceHolderItem, PlaceHolder.id == PlaceHolderItem.placeholder_id)
            .filter(PlaceHolder.id == placeholder_id)
            .filter(PlaceHolder.team_id == current_user.team_id)
        ).all()

        if not placeholder_data:
            raise NotFoundException(i18n.t("common.notFound"))

        placeholder_name = placeholder_data[0][0]

        placeholder_item = {
            attr_name: attr_value for _, attr_name, attr_value in placeholder_data
        }
        placeholder = Placeholder(**placeholder_item)

        template = self.db.exec(
            select(
                FormTemplate.id,
                FormTemplate.title,
                FormTemplate.content,
                FormTemplate.team_id,
            )
            .filter(FormTemplate.id == template_id)
            .filter(FormTemplate.team_id == current_user.team_id)
        ).first()

        return (
            form_job.id,
            template,
            {
                "name": placeholder_name,
                "placeholder": placeholder,
            },
            form_job.target_collection_id,
            form_job.exclude_collection_id,
            form_job.approach_ng_flag,
            form_job.schedule_at,
            form_job.max_resend_code,
            form_job.type_code,
            form_job.form_schedule_id,
        )
