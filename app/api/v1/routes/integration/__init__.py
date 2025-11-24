from fastapi import APIRouter

from app.api.base.deps import custom_generate_unique_id

from .salesforce import router as salesforce_router

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)

router.include_router(salesforce_router, prefix="/salesforce", tags=["salesforce"])
