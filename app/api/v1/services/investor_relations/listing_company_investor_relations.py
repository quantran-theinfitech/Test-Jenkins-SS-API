from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.investor_relations import InvestorRelationsBase
from external.s3 import S3Service
from sqlmodel import Session, func

from app.api.v1.schemas.recruits import RecruitBase
from app.models.company import Company
from app.models.company_investor_relations import CompanyInvestorRelations

def listing_company_investor_relations(
    db: Session, corporate_number: str, per_page: int, page: int
):
    s3_service = S3Service()
    res = []
    investor_relations = (
        db.query(CompanyInvestorRelations)
        .filter(CompanyInvestorRelations.corporate_number == corporate_number)
        .order_by(CompanyInvestorRelations.ir_date.desc().nulls_last())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    for investor_relation in investor_relations:
        presigned_url = s3_service.generate_presigned_url_from_s3_uri(
            investor_relation.ir_s3_url
        )
        investor_relation = InvestorRelationsBase(
            ir_id=investor_relation.ir_id,
            ir_title=investor_relation.ir_title,
            corporate_number=investor_relation.corporate_number,
            ir_s3_url=presigned_url,
            ir_company_name=investor_relation.ir_company_name,
            ir_date=investor_relation.ir_date,
            created_at=investor_relation.created_at,
            created_by=investor_relation.created_by,
            updated_at=investor_relation.updated_at,
        )
        res.append(investor_relation)
    return res


def listing_company_investor_relations_count(db: Session, corporate_number: str):
    investor_relations_count = (
        db.query(func.count(CompanyInvestorRelations.corporate_number))
        .filter(CompanyInvestorRelations.corporate_number == corporate_number)
        .scalar()
    )
    return investor_relations_count

def download_ir_file(db: Session, s3_service: S3Service, ir_id: str):
    investor_relation = (
        db.query(CompanyInvestorRelations)
        .filter(CompanyInvestorRelations.ir_id == ir_id)
        .first()
    )

    if not investor_relation:
        raise NotFoundException(detail="common.notFound")

    s3_uri = investor_relation.ir_s3_url
    if not s3_uri:
        raise NotFoundException(detail="common.notFound")

    # Download file về local
    local_path = s3_service.download_file(s3_uri)
    return local_path
