from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.teams import TeamMemberBase, UpdateTeamRequest
from app.api.v1.schemas.users import UserBase
from app.models.user import TeamMemberRoleCode, User


def update_team_member_role(
    db: Session, current_user: UserBase, request: UpdateTeamRequest
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
    users = db.exec(
        select(User).where(
            User.id.in_(id_list),
            User.deleted_at.is_(None),
            User.team_id == current_user.team_id,
        )
    ).all()
    for user in users:
        user.team_member_role_code = mapping.get(user.id)
    db.commit()
    for user in users:
        db.refresh(user)
    return TeamMemberBase(team_member_list=users)
