from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.todos import UpdateTodoRequest
from app.models.activity_log import ActivityLog, ModelCode
from app.models.todo import Todo
from app.models.user import User


def update_todo(db: Session, id: int, request: UpdateTodoRequest, current_user: User):
    todo = db.exec(
        select(Todo).where(Todo.team_id == current_user.team_id).where(Todo.id == id)
    ).first()
    activity_log = db.exec(
        select(ActivityLog)
        .where(ActivityLog.team_id == current_user.team_id)
        .where(ActivityLog.model_id == id)
        .where(ActivityLog.model_code == ModelCode.TODO)
    ).first()
    if not todo or not activity_log:
        raise NotFoundException(detail="todo.notFound")
    try:
        for attr, value in request.items():
            if attr in Todo.__fields__.keys():
                setattr(todo, attr, value)
        db.add(todo)
        db.flush()
        for attr, value in request.items():
            if attr in ActivityLog.__fields__.keys():
                setattr(activity_log, attr, value)
        db.add(activity_log)
        db.commit()
        db.refresh(todo)
        return todo.id
    except Exception as e:
        db.rollback()
        raise e
