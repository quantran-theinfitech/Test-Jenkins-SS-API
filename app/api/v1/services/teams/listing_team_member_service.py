from typing import Optional

from sqlmodel import Session, func, select

from app.api.v1.schemas.teams import ListingTeamMember
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.media import get_presigned_url
from app.models.user import RoleCode, User


def listing_team_member(
    db: Session,
    current_user: UserBase,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):

    total = db.exec(
        select(func.count()).where(
            User.team_id == current_user.team_id,
            User.role_code == RoleCode.User,
            User.deleted_at.is_(None),
        )
    ).first()

    team_members = (
        db.query(User)
        .where(User.team_id == current_user.team_id)
        .where(
            User.role_code == RoleCode.User,
            User.deleted_at.is_(None),
        )
        .order_by(User.id)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    team_members = sorted(
        team_members, key=lambda u: 0 if u.id == current_user.id else 1
    )
    team_member_list = []
    for member in team_members:
        mb = UserBase(**member.dict())
        mb.avatar_path = get_presigned_url(mb.avatar_path if mb.avatar_path else None)
        team_member_list.append(mb)
    return ListingTeamMember(
        team_member_list=team_member_list,
        total=total,
        page=page,
        per_page=per_page,
    )
