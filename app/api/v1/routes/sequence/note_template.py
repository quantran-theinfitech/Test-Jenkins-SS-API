from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.sequence.note import (
    CreateNoteRequest,
    GetNoteDetailResponse,
    UpdateNoteRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences import note_template as note_template_service

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/note_templates/{note_template_id}",
    response_model=GetNoteDetailResponse,
)
def get_note_templates_details(
    note_template_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return note_template_service.get_note_template_service(
        db, current_user, note_template_id
    )


@router.post("/note_templates")
def create_note_templates(
    request: CreateNoteRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return note_template_service.create_note_template_service(db, current_user, request)


@router.put("/note_templates/{note_template_id}")
def update_note_templates(
    note_template_id: int,
    request: UpdateNoteRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return note_template_service.update_note_template_service(
        db, current_user, note_template_id, request
    )
