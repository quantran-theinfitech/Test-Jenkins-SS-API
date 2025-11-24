from typing import List

from sqlmodel import Session, and_

from app.api.v1.schemas.activity_logs import ActivityLogBase
from app.api.v1.schemas.users import UserBase
from app.models.activity_log import ActivityLog
from app.models.todo import Todo
from app.models.user import User


class ActivityLogsService:
    def __init__(self, db: Session):
        self.db = db

    def listing_activity_logs(
        self, current_user: UserBase, corporate_number: str
    ) -> List[ActivityLogBase]:
        try:
            query_data = (
                self.db.query(
                    Todo,
                    User,
                )
                .join(
                    ActivityLog,
                    and_(
                        ActivityLog.model_id == Todo.id,
                        ActivityLog.model_code == "TODO",
                    ),
                )
                .outerjoin(
                    User, and_(Todo.assignee_id == User.id, User.deleted_at.is_(None))
                )
                .filter(
                    Todo.corporate_number == corporate_number,
                    Todo.team_id == current_user.team_id,
                )
                .order_by(Todo.plan_at.desc())
                .all()
            )

            data = []
            for row in query_data:
                todo, user = row
                data.append(
                    ActivityLogBase(
                        assignee_id=user.id if user else None,
                        assignee_name=user.name if user else None,
                        id=todo.id,
                        title=todo.title,
                        content=todo.content,
                        memo=todo.memo,
                        plan_at=todo.plan_at,
                        corporate_number=todo.corporate_number,
                        customer_name=todo.customer_name,
                        type_code=todo.type_code,
                        status_code=todo.status_code,
                        team_id=todo.team_id,
                    )
                )

            return data
        except Exception as e:
            print("Error in listing activity logs:", str(e))
            raise e
