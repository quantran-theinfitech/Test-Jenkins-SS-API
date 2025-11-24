from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import BadRequestException, ConflictException
from app.api.v1.schemas.integration.salesforce import (
    SalesforceIntegrationDetailResponse,
    SalesforceIntegrationResponse,
)
from app.api.v1.schemas.users import UserBase
from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.models.integration.salesforce.salesforce_company_field_mappings import (
    SalesforceCompanyFieldMappings,
)
from app.models.integration.salesforce.salesforce_field_mappings_default import (
    SalesforceFieldMappingDefault,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.team import Team
from utils.integration.salesforce import SalesforceService, get_token_salesforce


def create_salesforce_integration(
    authentication_code: str,
    is_reconnect: Optional[bool],
    db: Session,
    current_user: UserBase,
):
    try:
        access_token, refresh_token, instance_url, id_url = get_token_salesforce(
            authentication_code
        )

        if not access_token:
            raise BadRequestException(detail="integration.salesforce.connectFailed")

        salesforce_service = SalesforceService(
            access_token=access_token,
            refresh_token=refresh_token,
            instance_url=instance_url,
            id_url=id_url,
        )

        # Check if API is enabled for the Salesforce organization
        salesforce_service.check_api_enabled()

        response_data = salesforce_service.get_user_info()

        has_integration = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.salesforce_team_id
                == response_data["organization_id"],
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()

        if not is_reconnect and has_integration:
            raise ConflictException(
                detail="integration.salesforce.hasConnectedWithOtherTeam"
            )

        if is_reconnect:
            has_integration_another = db.exec(
                select(SalesforceIntegrations).where(
                    SalesforceIntegrations.team_id == current_user.team_id,
                    SalesforceIntegrations.deleted_at.is_(None),
                )
            ).first()

            if has_integration_another:
                if has_integration and (
                    has_integration_another.salesforce_team_id
                    != has_integration.salesforce_team_id
                ):
                    raise ConflictException(
                        detail="integration.salesforce.hasConnectedWithOtherTeam"
                    )
                has_integration_another.deleted_at = datetime.now()
                db.add(has_integration_another)
                db.flush()

        salesforce_integration = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.team_id == current_user.team_id,
                SalesforceIntegrations.salesforce_team_id
                == response_data["organization_id"],
            )
        ).first()

        if not salesforce_integration:
            salesforce_integration = SalesforceIntegrations(
                salesforce_team_id=response_data["organization_id"],
                team_id=current_user.team_id,
                email=response_data["email"],
                access_token=access_token,
                refresh_token=refresh_token,
                deleted_at=None,
                code=authentication_code,
                instance_url=instance_url,
                id_url=id_url,
                auto_pull_companies=True,
                auto_pull_persons=True,
                auto_sync_companies=True,
            )
            db.add(salesforce_integration)
            db.flush()
            db.refresh(salesforce_integration)

            mappings = db.exec(
                select(SalesforceFieldMappingDefault).where(
                    SalesforceFieldMappingDefault.is_suggested_field.isnot(True),
                    SalesforceFieldMappingDefault.deleted_at.is_(None),
                )
            ).all()

            for mapping in mappings:
                new_mapping = SalesforceCompanyFieldMappings(
                    salesforce_integration_id=salesforce_integration.id,
                    salesforce_team_id=salesforce_integration.salesforce_team_id,
                    salesforce_field=mapping.salesforce_field,
                    field=mapping.salesmart_field,
                    team_id=current_user.team_id,
                    field_class=mapping.field_class,
                    overwrite_flag=mapping.is_over_write,
                    autofill_flag=mapping.is_auto_fill,
                )
                db.add(new_mapping)
                db.flush()
        elif (
            salesforce_integration and salesforce_integration.deleted_at
        ) or is_reconnect:
            salesforce_integration.email = response_data["email"]
            salesforce_integration.access_token = access_token
            salesforce_integration.refresh_token = refresh_token
            salesforce_integration.deleted_at = None
            salesforce_integration.code = authentication_code
            salesforce_integration.instance_url = instance_url
            salesforce_integration.id_url = id_url
            db.add(salesforce_integration)
            db.flush()

        team = db.exec(select(Team).where(Team.id == current_user.team_id)).first()
        if team:
            team.integrated_platform = INTEGRATION_PLATFORM_ENUM["SALESFORCE"]
            db.add(team)

        db.commit()

        return SalesforceIntegrationResponse(
            connection_id=salesforce_integration.id,
            email=salesforce_integration.email,
            salesforce_team_id=salesforce_integration.salesforce_team_id,
            status=True,
        )
    except HTTPException as e:
        print("_______ error create_salesforce_integration _______", str(e))
        raise e


def disconnect_salesforce_integration(db: Session, current_user: UserBase):
    try:
        salesforce_integration = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.team_id == current_user.team_id,
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()

        if not salesforce_integration:
            raise BadRequestException(
                detail="integration.salesforce.notFoundConnection"
            )

        salesforce_integration.deleted_at = datetime.now()
        db.add(salesforce_integration)

        team = db.exec(select(Team).where(Team.id == current_user.team_id)).first()
        if team:
            team.integrated_platform = None
            db.add(team)

        db.commit()

        return SalesforceIntegrationResponse(
            connection_id=salesforce_integration.id,
            email=salesforce_integration.email,
            salesforce_team_id=salesforce_integration.salesforce_team_id,
            status=False,
        )
    except Exception:
        db.rollback()
        raise BadRequestException(detail="integration.salesforce.disconnectFailed")


def get_salesforce_integration_detail(
    db: Session, current_user: UserBase
) -> SalesforceIntegrationDetailResponse:
    salesforce_integration = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_integration:
        raise BadRequestException(detail="integration.salesforce.notFoundConnection")

    salesforce_service = SalesforceService(
        access_token=salesforce_integration.access_token,
        refresh_token=salesforce_integration.refresh_token,
        instance_url=salesforce_integration.instance_url,
        id_url=salesforce_integration.id_url,
    )

    salesforce_service.refresh_client()

    return SalesforceIntegrationDetailResponse(
        email=salesforce_integration.email,
        salesforce_team_id=salesforce_integration.salesforce_team_id,
    )
