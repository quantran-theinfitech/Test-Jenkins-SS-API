from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from sqlmodel import Session, select

from app.api.v1.queries.recruit import build_es_query
from app.api.v1.schemas.elasticsearch.recruits import ESRecruit
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from utils.mask_recruit_data import mask_recruit_data


def make_offset_recruit_data(recruits):
    recruits_data = []
    for data in recruits:
        if data.get("recruit_tels") and len(data.get("recruit_tels")) == 0:
            data["recruit_tels"] = (
                [data["recruit_phone"]] if data.get("recruit_phone") else None
            )
        else:
            data["recruit_tels"] = data.get("recruit_tels")
        if data.get("recruit_mails") and len(data.get("recruit_mails")) == 0:
            data["recruit_mails"] = (
                [data["recruit_email"]] if data.get("recruit_email") else None
            )
        else:
            data["recruit_mails"] = data.get("recruit_mails")
        data["company_tel"] = data.get("phone")
        data["contact_email"] = data.get("contact_email")
        data["hp_url"] = data.get("hp_url")
        data["contact_form_url"] = data.get("contact_form_url")
        recruits_data.append(data)

    return recruits_data


def search_recruits(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client: Elasticsearch,
    page: int,
    per_page: int,
    listing_plan_code: PlanCode,
    current_user: UserBase,
):

    search = ESRecruit.search(using=es_client, index=ESRecruit.Index.name)
    search_query = build_es_query(search_condition, db, current_user)
    exist_query = [{"exists": {"field": "title", "boost": 2}}]
    search_query = Q(
        "bool", must=search_query, should=exist_query, minimum_should_match=0
    )
    search: Search = search.query(search_query)
    size = 0
    if (10000 - ((page - 1) * per_page)) < 15:
        size = 10000 - ((page - 1) * per_page)
    else:
        size = per_page

    pagination_param = {
        "size": size,
        "from": (page - 1) * per_page,
        "track_total_hits": True,
    }
    corporate_numbers_downloaded = db.exec(
        select(TeamCompany.corporate_number).where(
            TeamCompany.team_id == current_user.team_id,
        )
    ).all()
    result = search.extra(**pagination_param).execute()["hits"]
    data = result["hits"]._l_
    total = result._d_["total"]["value"]
    recruits = [x["_source"] for x in data]
    for recruit in recruits:
        company = recruit["companies"][0]
        recruit["company_name"] = company["name"]
        recruit["company_tel"] = company["phone"]
        recruit["contact_email"] = company["contact_email"]
        recruit["job_positions"] = recruit["positions"]
        recruit["job_categories"] = recruit["categories"]
        recruit["company_downloaded_flag"] = (
            True
            if recruit["corporate_number"] in corporate_numbers_downloaded
            else False
        )
        recruit = mask_recruit_data(recruit, corporate_numbers_downloaded)
    if listing_plan_code == PlanCode.UNLIMITED:
        for recruit in recruits:
            recruit["downloaded_flag"] = True
    return recruits, min(total, 10000), total
