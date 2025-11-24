from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.schemas.search_all import SearchAllResponse, SearchType
from app.api.v1.services.search_all import search_all_service

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=SearchAllResponse)
def search_all(
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    keyword: str = Query(None),
    type: SearchType = Query(None),
):
    data = search_all_service(db, es_client, keyword, type)
    return SearchAllResponse(keyword=keyword, data=data)
