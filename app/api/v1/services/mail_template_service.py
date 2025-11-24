import datetime
from typing import Optional

from sqlalchemy import and_, distinct, func, text
from sqlmodel import Session, select

from app.api.v1.schemas.mail_templates import MailTemplateRequest
from app.models.mail_template import MailTemplate
from app.models.user import User


class MailTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def listing_mail_templates(
        self,
        current_user: User,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ):
        query = """SELECT COUNT(mj.template_id) AS job_number, mt.id ,
                    mt.title , mt."content" ,mt.team_id, mt .created_at ,
                    mt.created_by, MAX(mj.created_at)  AS last_used_at,
                    MAX(u."name") AS author
                    FROM mail_templates mt
                    LEFT JOIN mail_jobs mj ON mt.id = mj.template_id
                    LEFT JOIN users u ON mt.created_by = u.id
                    WHERE mt.team_id = :team_id
                    GROUP BY mt.id
                    ORDER BY mt.created_at DESC"""

        params = {"team_id": current_user.team_id}

        if page is not None and per_page is not None:
            query += " LIMIT :per_page OFFSET :offset"
            params["per_page"] = per_page
            params["offset"] = (page - 1) * per_page

        data = self.db.execute(
            text(query),
            params,
        ).all()

        return data

    def count_listing_mail_templates(self, current_user: User):
        total_query = select(MailTemplate).where(
            MailTemplate.team_id == current_user.team_id
        )
        total = (
            self.db.execute(
                total_query.with_only_columns(func.count(distinct(MailTemplate.id)))
            ).scalar()
            or 0
        )

        return total

    def get_mail_template_detail(self, mail_template_id: int, current_user: User):
        query = f""" SELECT mt.id, mt.title, mt."content", team_id
                     FROM mail_templates mt
                     WHERE mt.team_id = {current_user.team_id}
                     AND mt.id = {mail_template_id}"""
        data = self.db.execute(text(query)).first()
        return data

    def create_mail_template(self, request: MailTemplateRequest, current_user: User):
        new_mail_template = MailTemplate(
            title=request.title,
            content=request.content,
            team_id=current_user.team_id,
            created_by=current_user.id,
        )
        self.db.add(new_mail_template)
        self.db.commit()
        self.db.refresh(new_mail_template)
        return new_mail_template

    def edit_mail_template(
        self, mail_template_id: int, request: MailTemplateRequest, current_user: User
    ):
        mail_template = self.db.exec(
            select(MailTemplate).where(
                and_(
                    MailTemplate.id == mail_template_id,
                    MailTemplate.team_id == current_user.team_id,
                )
            )
        ).one()
        if request.title:
            mail_template.title = request.title
        if request.content:
            mail_template.content = request.content
        if request.content or request.title:
            mail_template.updated_by = current_user.id
            mail_template.updated_at = datetime.datetime.now()

        self.db.add(mail_template)
        self.db.commit()
        self.db.refresh(mail_template)
        return mail_template
