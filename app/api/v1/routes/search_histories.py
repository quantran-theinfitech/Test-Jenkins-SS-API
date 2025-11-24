from typing import Optional, List

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.api.base.deps import get_db, custom_generate_unique_id
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.search_histories import (
    ListSearchHistoriesResponse,
    SEARCH_HISTORY_ENUM,
    SearchHistoryItem,
    CreateSearchHistoryRequest
)
from app.api.v1.services.search_history_service import SearchHistoryService
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)

@router.get("", response_model=ListSearchHistoriesResponse)
def list_search_histories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user()),
    type: Optional[SEARCH_HISTORY_ENUM] = Query(
        None, 
        description="Filter by search type (PERSON/COMPANY)"
    ),
    q: Optional[str] = Query(
        None, 
        description="Search keyword in prompt message"
    )
):
    service = SearchHistoryService(db)
    search_histories = service.get_search_histories(
        current_user=current_user,
        type=type,
        q=q
    )
    
    return ListSearchHistoriesResponse(items=search_histories)


@router.post(
    "", 
    status_code=status.HTTP_201_CREATED,
    response_model=SearchHistoryItem
    )
def create_search_history(
    request: CreateSearchHistoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    service = SearchHistoryService(db)
    search_history = service.create_search_histories(
        current_user=current_user,
        prompt_message=request.prompt_message,
        type=request.type,
        team_id=request.team_id
    )
    return search_history
