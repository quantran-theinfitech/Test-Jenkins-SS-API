from typing import List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.connections as connection_service
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.connections import SlackConnectionItem, SlackConnectionResponse
from app.api.v1.schemas.users import UserBase

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/slack", response_model=SlackConnectionResponse)
def create_slack_connection(
    code: str = Query(default=""),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return connection_service.create_slack_connection(code, db, current_user)


@router.delete("/slack/{connection_id}", response_model=int)
def delete_slack_connection(
    connection_id: int,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return connection_service.delete_slack_connection(connection_id, db, current_user)


@router.get("", response_model=List[SlackConnectionItem])
def listing_slack_connections(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return connection_service.listing_slack_connections(db, current_user)
