from typing import Optional

from elasticsearch_dsl import Q, Search
from sqlmodel import Session, select

from app.api.v1.schemas.companies import CompanyByKeywordResponse
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from utils.extract_domain import (
    extract_full_domain_url,
    normalize_url,
    split_string_by_newline,
)
from utils.optimize_name import optimize_name


def get_company_by_keyword(
    db: Session,
    keyword: str,
    listing_plan_code: PlanCode,
    es_client,
    per_page: Optional[int],
    page: Optional[int],
):
    search = EsCompanyExtend.search(using=es_client, index=EsCompanyExtend.Index.name)
    must_queries = []
    queries = []

    if keyword:
        fields = ["name", "kana_name", "english_name"]
        or_name_es_query = [
            Q(
                "multi_match",
                query=optimize_name(x),
                fields=fields,
                type="best_fields",
            )
            for x in split_string_by_newline(keyword)
        ]
        or_name_es_query.extend(
            Q("multi_match", query=x, fields=fields, type="best_fields")
            for x in split_string_by_newline(keyword)
        )
        or_name_es_query.append(
            Q("wildcard", domain={"value": normalize_url(keyword), "boost": 30.0})
        )
        queries.append(Q("bool", should=or_name_es_query))
        must_queries.extend(queries)

    exist_query = [
        {"exists": {"field": "domain", "boost": 2}},
        {"exists": {"field": "name", "boost": 2}},
    ]

    final_query = Q("bool", must=must_queries)
    search_query = Q(
        "bool", must=final_query, should=exist_query, minimum_should_match=0
    )
    size = 10
    pagination_param = {
        "size": size,
        "from": ((page or 1) - 1) * (per_page or 10),
        "track_total_hits": True,
    }

    search: Search = search.query(search_query)
    search = search.params(request_timeout=30)
    result = search.extra(**pagination_param).execute()
    companies = []
    for hit in result:
        if "name" in hit and "corporate_number" in hit:
            # Tạo favicon_url với /favicon.ico từ hp_url
            domain_url = extract_full_domain_url(hit["hp_url"])
            if domain_url:
                favicon_url = f"{domain_url}/favicon.ico"
            else:
                favicon_url = None

            if listing_plan_code == PlanCode.UNLIMITED:
                is_downloaded = True
            else:
                company_downloaded = db.exec(
                    select(TeamCompany).where(
                        TeamCompany.corporate_number == hit.corporate_number
                    )
                ).all()
                is_downloaded = len(company_downloaded) > 0
            companies.append(
                {
                    "name": hit.name,
                    "corporate_number": hit.corporate_number,
                    "domain": hit.domain,
                    "hp_url": hit.hp_url,
                    "downloaded_flag": is_downloaded,
                    "favicon_url": favicon_url,
                    "president_name": hit.president_name,
                }
            )

    return CompanyByKeywordResponse(data=companies)
