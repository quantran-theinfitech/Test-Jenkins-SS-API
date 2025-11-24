import datetime
import re
from json import dumps, loads
from typing import Dict, Any

import requests
from sqlmodel import Session, col, select

from app.api.base.exceptions import ConflictException, NotFoundException
from app.config import settings
from app.api.v1.schemas.companies import SaveSearchConditionRequest
from app.api.v1.schemas.search_conditions import (
    RefineQueryRequest,
    RefineQueryResponse,
    UpdateSearchConditionRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.search_condition import OwnerCodeCondition, SearchCondition


class SearchConditionService:
    def __init__(self, db: Session):
        self.db = db

    def listing_search_conditions(self, current_user: UserBase):
        list_condition = (
            self.db.query(SearchCondition)
            .where(SearchCondition.user_id == current_user.id)
            .where(SearchCondition.deleted_at.is_(None))
            .order_by(col(SearchCondition.id).desc())
            .all()
        )
        return list_condition

    def get_search_condition_detail(self, condition_id: int, current_user: UserBase):
        search_condition = (
            self.db.query(SearchCondition)
            .where(SearchCondition.id == condition_id)
            .where(SearchCondition.user_id == current_user.id)
            .where(SearchCondition.deleted_at.is_(None))
            .first()
        )

        if not search_condition:
            raise NotFoundException(detail="common.notFound")

        return search_condition

    def save_search_condition(
        self,
        condition_request: SaveSearchConditionRequest,
        current_user: UserBase,
    ):
        save_search = self.db.exec(
            select(SearchCondition)
            .where(SearchCondition.name == condition_request.name)
            .where(SearchCondition.user_id == current_user.id)
            .where(SearchCondition.deleted_at.is_(None))
        ).first()
        if save_search:
            raise ConflictException(detail="auth.conditionAlreadyExist")
        new_search_condition = SearchCondition(
            user_id=current_user.id,
            owner_code=OwnerCodeCondition.USER,
            name=condition_request.name,
            conditions=loads(dumps(condition_request.conditions.dict(), default=str)),
            created_by=current_user.id,
        )
        self.db.add(new_search_condition)
        self.db.commit()
        return new_search_condition

    def delete_search_condition(self, search_condition_id: int, current_user: UserBase):
        try:
            search_condition = (
                self.db.exec(
                    select(SearchCondition)
                    .where(SearchCondition.user_id == current_user.id)
                    .where(SearchCondition.id == search_condition_id)
                    .where(SearchCondition.deleted_at.is_(None))
                )
            ).first()

            if not search_condition:
                raise NotFoundException(detail="common.notFound")

            search_condition.deleted_by = current_user.id
            search_condition.deleted_at = datetime.datetime.now()

            self.db.add(search_condition)
            self.db.commit()
            self.db.refresh(search_condition)

        except Exception as e:
            self.db.rollback()
            raise e
        return search_condition

    def update_search_condition(
        self,
        search_condition_id: int,
        current_user: UserBase,
        request: UpdateSearchConditionRequest,
    ):
        try:
            search_condition = self.db.exec(
                select(SearchCondition)
                .where(SearchCondition.user_id == current_user.id)
                .where(SearchCondition.id == search_condition_id)
                .where(SearchCondition.deleted_at.is_(None))
            ).first()

            listing_search_conditions = self.listing_search_conditions(current_user)
            for condition in listing_search_conditions:
                if (
                    condition.name == request.name
                    and condition.id != search_condition_id
                ):
                    raise ConflictException(detail="auth.conditionAlreadyExist")

            if not search_condition:
                raise NotFoundException(detail="common.notFound")

            if request.name:
                search_condition.name = request.name

            if request.conditions:
                search_condition.conditions = loads(
                    dumps(request.conditions.dict(), default=str)
                )

            search_condition.updated_by = current_user.id
            search_condition.updated_at = datetime.datetime.now()

            self.db.add(search_condition)
            self.db.commit()
            self.db.refresh(search_condition)

        except Exception as e:
            self.db.rollback()
            raise e

        return search_condition

    def duplicate_search_condition(
        self, search_condition_id: int, current_user: UserBase
    ):
        try:
            search_condition = self.db.exec(
                select(SearchCondition)
                .where(SearchCondition.user_id == current_user.id)
                .where(SearchCondition.id == search_condition_id)
                .where(SearchCondition.deleted_at.is_(None))
            ).first()

            if not search_condition:
                raise NotFoundException(detail="common.notFound")

            base_name_match = re.match(
                r"^(.*?)(?: copy(?: (\d+))?)?$", search_condition.name
            )
            base_name = base_name_match.group(1)

            similar_names = self.db.exec(
                select(SearchCondition)
                .where(SearchCondition.user_id == current_user.id)
                .where(SearchCondition.name.ilike(f"{base_name} copy%"))
            ).all()

            max_copy = 0
            for sc in similar_names:
                match = re.match(rf"^{re.escape(base_name)} copy(?: (\d+))?$", sc.name)
                if match:
                    num = int(match.group(1)) if match.group(1) else 1
                    max_copy = max(max_copy, num)

            new_name = (
                f"{base_name} copy"
                if max_copy == 0
                else f"{base_name} copy {max_copy + 1}"
            )

            new_search_condition = SearchCondition(
                name=new_name,
                user_id=search_condition.user_id,
                conditions=search_condition.conditions,
                created_by=search_condition.user_id,
                owner_code=OwnerCodeCondition.USER,
            )
            self.db.add(new_search_condition)
            self.db.commit()
            self.db.refresh(new_search_condition)

        except Exception as e:
            self.db.rollback()
            raise e

        return new_search_condition

    def refine_query(self, request: RefineQueryRequest, current_user: UserBase) -> RefineQueryResponse:
        """
        Refine a search query by calling external LangGraph API.
        """
        try:
            # Prepare the request payload
            payload = {
                "query": request.query,
                "type": request.type
            }
            
            # Prepare authentication
            auth = (settings.LANGGRAPH_USERNAME, settings.LANGGRAPH_PASSWORD)
            
            # Make the API call
            response = requests.post(
                f"{settings.LANGGRAPH_URL_API}/refine-query",
                json=payload,
                auth=auth,
                timeout=30  # 30 seconds timeout
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Return the response in the expected format
            return RefineQueryResponse(
                input_query=response_data.get("input_query", request.query),
                refined_query=response_data.get("refined_query", [])
            )
            
        except requests.exceptions.RequestException as e:
            # Log the error and return a fallback response
            # In production, you might want to use a proper logging system
            print(f"Error calling LangGraph API: {str(e)}")
            
            # Return a fallback response
            return RefineQueryResponse(
                input_query=request.query,
                refined_query=[f"- {request.query}"]
            )
        except Exception as e:
            # Handle any other unexpected errors
            print(f"Unexpected error in refine_query: {str(e)}")
            
            # Return a fallback response
            return RefineQueryResponse(
                input_query=request.query,
                refined_query=[f"- {request.query}"]
            )
