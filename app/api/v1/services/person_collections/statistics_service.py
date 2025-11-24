from elasticsearch_dsl import Q
from sqlmodel import Session

from app.api.v1.queries.person import build_es_query
from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.person_collections import CreatePersonCollectionRequest
from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode


def statistics_by_condition(
    db: Session,
    request: CreatePersonCollectionRequest,
    current_user: UserBase,
    listing_plan_code: PlanCode,
    es_client,
):
    try:
        search = ESPersonExtend.search(using=es_client, index=ESPersonExtend.Index.name)
        search = search.source(["uuid"])
        search_query = build_es_query(request)

        if listing_plan_code is not PlanCode.UNLIMITED:
            queries = []
            queries.append(search_query)
            queries.append(Q("term", team_ids=current_user.team_id))
            collection_item_query = Q("bool", must=queries)
        else:
            collection_item_query = search_query

        search = search.query(collection_item_query)
        pagination_param = {"size": 0, "track_total_hits": True}
        result = search.extra(**pagination_param).execute()["hits"]
        total = result._d_["total"]["value"]
        return total
    except Exception as e:
        db.rollback()
        raise e
