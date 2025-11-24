import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.api.v1.schemas.hubspot_connections import HubspotConnectionResponse
from app.api.v1.schemas.users import UserBase
from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.models import HubspotIntergrations
from app.models.integration.hubspot.field_mapping_hubspot import FieldMappingHubspot
from app.models.integration.hubspot.hubspot_company_field_mappings import (
    HubspotCompanyFieldMappings,
)
from app.models.team import Team
from utils.hubspot_connection import HubSpotService, get_token_hubspot


def create_hubspot_connection(
    authentication_code: str,
    is_reconnect: Optional[bool],
    db: Session,
    current_user: UserBase,
) -> HubspotConnectionResponse:
    try:

        access_token, refresh_token = get_token_hubspot(authentication_code)

        if not access_token:
            raise ConflictException(detail="integration.hubspot.connectFailed")

        hubspot_service = HubSpotService(
            access_token=access_token, refresh_token=refresh_token
        )
        response_data = hubspot_service.get_user_info()

        if not is_reconnect:
            has_integration = db.exec(
                select(HubspotIntergrations).where(
                    HubspotIntergrations.hubspot_team_id == response_data["hub_id"],
                    HubspotIntergrations.deleted_at.is_(None),
                )
            ).first()

            if has_integration:
                raise ConflictException(
                    detail="integration.hubspot.hasConnectedWithOtherTeam"
                )
        else:
            has_integration_another_account = db.exec(
                select(HubspotIntergrations).where(
                    HubspotIntergrations.team_id == current_user.team_id,
                    HubspotIntergrations.deleted_at.is_(None),
                )
            ).first()
            if has_integration_another_account:
                has_integration_another_account.deleted_at = datetime.now()
                db.add(has_integration_another_account)
                db.flush()

        hubspot_integration = db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.team_id == current_user.team_id,
                HubspotIntergrations.hubspot_team_id == response_data["hub_id"],
            )
        ).first()

        if not hubspot_integration:
            hubspot_integration = HubspotIntergrations(
                hubspot_team_id=response_data["hub_id"],
                team_id=current_user.team_id,
                email=response_data["user"],
                access_token=access_token,
                refresh_token=refresh_token,
                code=authentication_code,
                auto_pull_companies=True,
                auto_pull_persons=True,
                auto_sync_companies=True,
            )
            db.add(hubspot_integration)
            db.flush()
            db.refresh(hubspot_integration)

            mappings = db.exec(
                select(FieldMappingHubspot).where(
                    FieldMappingHubspot.is_suggested_field.isnot(True),
                    FieldMappingHubspot.deleted_at.is_(None),
                )
            ).all()

            for mapping in mappings:
                new_mapping = HubspotCompanyFieldMappings(
                    integration_id=hubspot_integration.id,
                    hubspot_team_id=hubspot_integration.hubspot_team_id,
                    hubspot_field=mapping.hubspot_field,
                    field=mapping.sale_smart_field,
                    overwrite_flag=mapping.is_over_write,
                    autofill_flag=mapping.is_auto_fill,
                )
                db.add(new_mapping)
        elif hubspot_integration.deleted_at or is_reconnect:
            hubspot_integration.hubspot_team_id = response_data["hub_id"]
            hubspot_integration.team_id = current_user.team_id
            hubspot_integration.email = response_data["user"]
            hubspot_integration.code = authentication_code
            hubspot_integration.access_token = access_token
            hubspot_integration.refresh_token = refresh_token
            hubspot_integration.deleted_at = None
        else:
            raise ConflictException(detail="integration.hubspot.alreadyConnected")

        team = db.exec(select(Team).where(Team.id == current_user.team_id)).first()
        if team:
            team.integrated_platform = INTEGRATION_PLATFORM_ENUM["HUBSPOT"]
            db.add(team)

        db.commit()

        return HubspotConnectionResponse(
            connection_id=hubspot_integration.id,
            email=hubspot_integration.email,
            hubspot_team_id=str(hubspot_integration.hubspot_team_id),
            status=True,
        )
    except HTTPException as e:
        db.rollback()
        raise e


def disconnect_hubspot_connection(db: Session, current_user: UserBase) -> int:
    try:
        hubspot_integration = db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.team_id == current_user.team_id,
                HubspotIntergrations.deleted_at.is_(None),
            )
        ).first()

        if not hubspot_integration:
            raise NotFoundException(detail="integration.hubspot.notFoundConnection")
        hubspot_integration.deleted_at = datetime.datetime.now()
        db.add(hubspot_integration)

        team = db.exec(select(Team).where(Team.id == current_user.team_id)).first()
        if team:
            team.integrated_platform = None
            db.add(team)

        db.commit()
        return hubspot_integration.id

    except Exception:
        db.rollback()
        raise BadRequestException(detail="integration.hubspot.disconnectFailed")
