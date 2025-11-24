from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.api.v1.schemas.teams import (
    ListingTeamMember,
    TeamMemberBase,
    UpdateTeamRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.user import RoleCode, TeamMemberRoleCode, User


class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def listing_team_member(
        self,
        current_user: UserBase,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ):

        total = self.db.exec(
            select(func.count()).where(
                User.team_id == current_user.team_id,
                User.role_code == RoleCode.User,
            )
        ).first()

        team_members = (
            self.db.query(User)
            .where(User.team_id == current_user.team_id)
            .where(User.role_code == RoleCode.User)
            .order_by(User.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        team_members = sorted(
            team_members, key=lambda u: 0 if u.id == current_user.id else 1
        )
        return ListingTeamMember(
            team_member_list=team_members,
            total=total,
            page=page,
            per_page=per_page,
        )

    def update_team_member_role(
        self, current_user: UserBase, request: UpdateTeamRequest
    ):
        if current_user.team_member_role_code != TeamMemberRoleCode.MANAGER.value:
            raise HTTPException(
                status_code=403,
                detail="auth.permissionDenied",
            )
        update_list = request.update_role_list
        mapping = {}
        id_list = []
        for user in update_list:
            mapping[user.id] = user.team_member_role_code
            id_list.append(user.id)
        users = self.db.exec(
            select(User).where(
                User.id.in_(id_list),
                User.deleted_at.is_(None),
                User.team_id == current_user.team_id,
            )
        ).all()
        for user in users:
            user.team_member_role_code = mapping.get(user.id)
        self.db.commit()
        for user in users:
            self.db.refresh(user)
        return TeamMemberBase(team_member_list=users)
