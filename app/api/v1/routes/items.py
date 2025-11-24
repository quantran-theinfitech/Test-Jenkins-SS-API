from fastapi import APIRouter, Depends

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import has_paid_plan, has_plan
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/items", response_model=str)
def listing_items(plan_user_code: PlanCode = Depends(has_plan(PlanCode.PRE))):
    return "SUCCESS"


@router.post("/items", response_model=str)
def create_item(plan_user_code: PlanCode = Depends(has_paid_plan())):
    return "SUCCESS"
