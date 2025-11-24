from elasticsearch_dsl import Q, Search
from sqlmodel import Session, select

from app.api.v1.queries.company import build_es_query
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.models import Team
from app.models.team import PlanCode


def estimate_collection_items(
    db: Session,
    search_condition: SearchCrossRequest,
    current_user: UserBase,
    es_client,
):
    listing_plan_code = db.exec(
        select(Team.listing_plan_code).where(Team.id == current_user.team_id)
    ).one()

    search = EsCompanyExtend.search(using=es_client, index=EsCompanyExtend.Index.name)
    search_query = build_es_query(search_condition)
    if listing_plan_code is PlanCode.UNLIMITED:
        estimate_query = search_query
    else:
        queries = []
        queries.append(search_query)
        queries.append(Q("term", team_ids=current_user.team_id))
        estimate_query = Q("bool", must=queries)

    search: Search = search.query(estimate_query)
    pagination_param = {
        "size": 0,  # Just get the total, no data needed
        "from": 0,
        "track_total_hits": True,
    }
    result = search.extra(**pagination_param).execute()["hits"]
    total = result._d_["total"]["value"]

    return total
