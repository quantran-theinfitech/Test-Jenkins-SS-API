from functools import partial
from typing import Optional

from fastapi import Depends

from app.api.base.exceptions import ForbiddenException
from app.api.v1.dependencies import get_current_user, get_user_service
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.user_sevice import UserService
from app.models.plan import PlanServiceCode
from app.models.team import PaidCode, PlanCode


# Check team of user have paid plan with service_code, service_code default is LISTING
def has_paid_plan(
    service_code: Optional[PlanServiceCode] = PlanServiceCode.LISTING,
):
    return partial(has_paid_plan_impl, service_code)


# Check team of user have plan with service_code, service_code default is LISTING
def has_plan(
    plan_code: PlanCode,
    service_code: Optional[PlanServiceCode] = PlanServiceCode.LISTING,
):
    return partial(has_plan_impl, plan_code, service_code)


# get plan_code of user with service_code, service_code default is LISTING
def get_plan_code(
    service_code: Optional[PlanServiceCode] = PlanServiceCode.LISTING,
):
    return partial(get_plan_code_impl, service_code)


def check_active_platform():
    return partial(has_active_platform)


def get_platform():
    return partial(get_integrated_platform)


def has_plan_impl(
    plan_code: PlanCode,
    service_code: PlanServiceCode,
    user_service: UserService = Depends(get_user_service),
    current_user: UserBase = Depends(get_current_user()),
) -> PlanCode:
    user_plan_code = user_service.get_user_plan(current_user, service_code)
    if user_plan_code and user_plan_code == plan_code:
        return user_plan_code
    else:
        raise ForbiddenException(detail="team.teamHasNotPlan")


def get_plan_code_impl(
    service_code: PlanServiceCode,
    user_service: UserService = Depends(get_user_service),
    current_user: UserBase = Depends(get_current_user()),
):
    return user_service.get_user_plan(current_user, service_code)


def has_paid_plan_impl(
    service_code: PlanServiceCode,
    user_service: UserService = Depends(get_user_service),
    current_user: UserBase = Depends(get_current_user()),
) -> PlanCode:
    user_plan_code = user_service.get_user_plan(current_user, service_code)
    paid_plans = [plan.value for plan in PaidCode]
    if user_plan_code and user_plan_code.value in paid_plans:
        return user_plan_code
    else:
        raise ForbiddenException(detail="team.teamHasNotPaidPlan")


def has_active_platform(
    user_service: UserService = Depends(get_user_service),
    current_user: UserBase = Depends(get_current_user()),
):
    return user_service.get_active_platform(current_user)


def get_integrated_platform(
    user_service: UserService = Depends(get_user_service),
    current_user: UserBase = Depends(get_current_user()),
):
    return user_service.get_integrated_platform(current_user)
