from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.todos import CreateTodoRequest, UpdateTodoRequest
from app.api.v1.services.todos import create_todo_service, update_todo_service
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("", response_model=int)
def create_todo(
    request: CreateTodoRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user()),
):
    return create_todo_service.create_todo(db, request, current_user)


@router.patch("/{id}")
def update_todo(
    id: int,
    request: UpdateTodoRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user()),
):
    return update_todo_service.update_todo(
        db, id, request.dict(exclude_none=True), current_user
    )
