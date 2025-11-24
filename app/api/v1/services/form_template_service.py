import datetime
from typing import Optional

from sqlalchemy import and_, text
from sqlmodel import Session, select

from app.api.v1.schemas.form_templates import FormTemplateRequest
from app.models.form_template import FormTemplate
from app.models.user import User


class FormTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def listing_form_templates(
        self,
        current_user: User,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        keyword: Optional[str] = None,
    ):
        query_keyword = ""
        if keyword:
            query_keyword = """ AND ft.title ILIKE :keyword"""

        query_pagination = ""
        if page and per_page:
            query_pagination = """ LIMIT :limit OFFSET :offset"""

        query = f"""SELECT COUNT(fj.template_id) AS job_number, ft.id ,
                    ft.title , ft."content" ,ft.team_id, ft .created_at ,
                    ft.created_by, MAX(fj.created_at)  AS last_used_at,
                    MAX(u."name") AS author
                    FROM form_templates ft
                    LEFT JOIN form_jobs fj ON ft.id = fj.template_id
                    LEFT JOIN users u ON ft.created_by = u.id
                    WHERE ft.team_id = :team_id
                    {query_keyword}
                    GROUP BY ft.id
                    ORDER BY ft.created_at DESC
                    {query_pagination}
                """
        data = self.db.execute(
            text(query),
            {
                "team_id": current_user.team_id,
                "limit": per_page,
                "offset": (page - 1) * per_page if per_page and page else "",
                "keyword": f"%{keyword}%",
            },
        ).all()

        return data

    def count_listing_form_templates(
        self, current_user: User, keyword: Optional[str] = None
    ):

        query_keyword = ""
        if keyword:
            query_keyword = """ AND ft.title ILIKE :keyword """
        query = f""" SELECT count(*) FROM form_templates ft
                    WHERE ft.team_id = :team_id
                    {query_keyword}
        """
        total = (
            self.db.execute(
                text(query),
                {
                    "team_id": current_user.team_id,
                    "keyword": f"%{keyword}%",
                },
            ).scalar()
            or 0
        )

        return total

    def get_form_template_detail(self, form_template_id: int, current_user: User):
        query = f""" SELECT ft.id, ft.title, ft."content", team_id
                     FROM form_templates ft
                     WHERE ft.team_id = {current_user.team_id}
                     AND ft.id = {form_template_id}"""
        data = self.db.execute(text(query)).first()
        return data

    def create_form_template(self, request: FormTemplateRequest, current_user: User):
        new_form_template = FormTemplate(
            title=request.title,
            content=request.content,
            team_id=current_user.team_id,
            created_by=current_user.id,
        )
        self.db.add(new_form_template)
        self.db.commit()
        self.db.refresh(new_form_template)
        return new_form_template

    def edit_form_template(
        self, form_template_id: int, request: FormTemplateRequest, current_user: User
    ):
        form_template = self.db.exec(
            select(FormTemplate).where(
                and_(
                    FormTemplate.id == form_template_id,
                    FormTemplate.team_id == current_user.team_id,
                )
            )
        ).one()
        if request.title:
            form_template.title = request.title
        if request.content != form_template.content:
            form_template.content = request.content
        if request.content != form_template.content or request.title:
            form_template.updated_by = current_user.id
            form_template.updated_at = datetime.datetime.now()

        self.db.add(form_template)
        self.db.commit()
        self.db.refresh(form_template)
        return form_template
