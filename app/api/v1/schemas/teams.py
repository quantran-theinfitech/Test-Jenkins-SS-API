from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.api.v1.schemas.users import UserBase
from app.models.user import TeamMemberRoleCode


class TeamMemberBase(BaseModel):
    team_member_list: List[UserBase] = []


class ListingTeamMember(TeamMemberBase):
    total: int
    page: int
    per_page: int


class UserMemberRole(BaseModel):
    id: int
    team_member_role_code: Optional[TeamMemberRoleCode] = None


class UpdateTeamRequest(BaseModel):
    update_role_list: List[UserMemberRole] = []


class InviteMembersRequest(BaseModel):
    email: List[EmailStr] = Field(
        min_items=1, max_items=20, description="Invitee email addresses"
    )
    role: TeamMemberRoleCode = Field(min_length=1, description="Invitee role")


class ValidateInvitationTokenResponse(BaseModel):
    inviter_name: str
    inviter_email: str
    role: TeamMemberRoleCode
    is_new_user: bool


class AcceptInvitationResponse(BaseModel):
    register_token: Optional[str] = None
    team_id: Optional[int] = None
    company_name: Optional[str] = None


class RejectInvitationRequest(BaseModel):
    token: str


class AcceptInvitationRequest(BaseModel):
    token: str
