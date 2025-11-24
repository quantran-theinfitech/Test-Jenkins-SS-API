from sqlmodel import Session

from app.api.v1.schemas.todos import CreateTodoRequest
from app.models.activity_log import ActivityLog, ModelCode
from app.models.todo import Todo
from app.models.user import User


def create_todo(db: Session, request: CreateTodoRequest, current_user: User):
    try:
        new_todo = Todo(
            corporate_number=request.corporate_number,
            assignee_id=request.assignee_id,
            title=request.title,
            content=request.content,
            memo=request.memo,
            team_id=current_user.team_id,
            plan_at=request.plan_at,
            customer_name=request.customer_name,
            status_code=request.status_code,
            type_code=request.type_code,
        )
        db.add(new_todo)
        db.flush()
        new_activity_log = ActivityLog(
            corporate_number=new_todo.corporate_number,
            model_code=ModelCode.TODO,
            status_code=new_todo.status_code,
            team_id=new_todo.team_id,
            model_id=new_todo.id,
            memo=new_todo.memo,
        )
        db.add(new_activity_log)
        db.commit()
        db.refresh(new_todo)
        return new_todo.id
    except Exception as e:
        db.rollback()
        raise e
