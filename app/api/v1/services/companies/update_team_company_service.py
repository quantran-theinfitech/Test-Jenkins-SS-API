from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.companies import UpdateTeamCompanyRequest
from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode
from app.models.team_company import StatusCode, TeamCompany


def update_team_company(
    db: Session,
    corporate_number: str,
    request: UpdateTeamCompanyRequest,
    current_user: UserBase,
    listing_plan_code: PlanCode,
):
    team_company = db.exec(
        select(TeamCompany)
        .where(TeamCompany.team_id == current_user.team_id)
        .where(TeamCompany.corporate_number == corporate_number)
    ).first()

    if not team_company:
        if listing_plan_code is PlanCode.UNLIMITED:
            team_company = TeamCompany(
                team_id=current_user.team_id,
                corporate_number=corporate_number,
                status_code=StatusCode.PENDING,
                tags=request.tags,
            )
        else:
            raise NotFoundException(detail="company.companyNotFound")

    for attr, value in request.dict(exclude_unset=True).items():
        setattr(team_company, attr, value)

    db.add(team_company)
    db.commit()
    db.refresh(team_company)
    return team_company
