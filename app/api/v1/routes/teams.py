from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi_mail import ConnectionConfig
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session, mail_connection
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.teams import (
    AcceptInvitationRequest,
    AcceptInvitationResponse,
    InviteMembersRequest,
    ListingTeamMember,
    RejectInvitationRequest,
    TeamMemberBase,
    UpdateTeamRequest,
    ValidateInvitationTokenResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services import teams as team_services

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/members", response_model=ListingTeamMember)
def listing_team_members(
    page: Optional[int] = Query(default=1, ge=1),
    per_page: Optional[int] = Query(default=20, ge=10, le=50),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return team_services.listing_team_member(db, current_user, page, per_page)


@router.put("/members", response_model=TeamMemberBase)
def update_team_member(
    request: UpdateTeamRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return team_services.update_team_member_role(db, current_user, request)


@router.post("/invite-members", status_code=status.HTTP_201_CREATED)
def invite_members(
    request: InviteMembersRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    mail_connection: ConnectionConfig = Depends(mail_connection),
):
    return team_services.invite_members(
        db, current_user, request, background_tasks, mail_connection
    )


@router.get(
    "/validate-invitation-token", response_model=ValidateInvitationTokenResponse
)
def validate_invitation_token(
    token: str = Query(..., description="The token to check"),
    db: Session = Depends(get_session),
):
    res = team_services.validate_invitation_token(db, token)
    return ValidateInvitationTokenResponse(
        inviter_name=res["inviter_name"],
        inviter_email=res["inviter_email"],
        role=res["role"],
        is_new_user=res["is_new_user"],
    )


@router.patch("/reject-invitation", status_code=status.HTTP_200_OK)
def reject_invitation(
    request: RejectInvitationRequest,
    db: Session = Depends(get_session),
):
    return team_services.reject_invitation(db, request.token)


@router.patch("/accept-invitation", response_model=AcceptInvitationResponse)
def accept_invitation(
    request: AcceptInvitationRequest,
    db: Session = Depends(get_session),
):
    response = team_services.accept_invitation(db, request.token)
    if response is None:
        return AcceptInvitationResponse()
    return AcceptInvitationResponse(
        register_token=response["register_token"],
        team_id=response["team_id"],
        company_name=response["company_name"],
    )
