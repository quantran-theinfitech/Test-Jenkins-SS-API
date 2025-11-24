from typing import List, Optional

from sqlmodel import Session, delete, select

from app.api.v1.schemas.users import UserBase
from app.constant.constants import MAX_SEARCH_HISTORY_RECORDS
from app.models.search_history import SEARCH_HISTORY_ENUM, SearchHistory


class SearchHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_search_histories(
        self,
        current_user: UserBase,
        prompt_message: str,
        type: SEARCH_HISTORY_ENUM,
        team_id: Optional[int] = None,
    ) -> SearchHistory:
        search_history = SearchHistory(
            user_id=current_user.id,
            team_id=team_id or getattr(current_user, "team_id", None),
            prompt_message=prompt_message,
            type=type,
        )
        self.db.add(search_history)
        self.db.flush()

        latest_ids_query = (
            select(SearchHistory.id)
            .where(SearchHistory.user_id == current_user.id)
            .where(SearchHistory.type == type)
            .order_by(SearchHistory.created_at.desc())
            .limit(MAX_SEARCH_HISTORY_RECORDS)
        )

        latest_ids = [id for id in self.db.exec(latest_ids_query).all()]

        if latest_ids:
            delete_old_histories_query = (
                delete(SearchHistory)
                .where(SearchHistory.user_id == current_user.id)
                .where(SearchHistory.type == type)
                .where(SearchHistory.id.not_in(latest_ids))
            )
            self.db.exec(delete_old_histories_query)

        self.db.commit()
        self.db.refresh(search_history)
        return search_history

    def get_search_histories(
        self,
        current_user: UserBase,
        type: Optional[SEARCH_HISTORY_ENUM] = None,
        q: Optional[str] = None,
        max_records: int = MAX_SEARCH_HISTORY_RECORDS,
    ) -> List[SearchHistory]:
        search_history_query = (
            select(SearchHistory)
            .where(SearchHistory.user_id == current_user.id)
            .order_by(SearchHistory.created_at.desc())
        )

        if type is not None:
            search_history_query = search_history_query.where(
                SearchHistory.type == type
            )

        if q and q.strip():
            search_history_query = search_history_query.where(
                SearchHistory.prompt_message.ilike(f"%{q}%")
            )

        search_history_query = search_history_query.limit(max_records)

        return self.db.exec(search_history_query).all()
