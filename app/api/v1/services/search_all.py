# flake8: noqa: E501
from typing import List

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from sqlmodel import Session

from app.api.v1.schemas.elasticsearch.recruits import ESRecruit
from app.api.v1.schemas.search_all import SearchAllBase, SearchType


def split_string_by_comma(string: str) -> List[str]:
    return string.split(",")


def search_all_service(
    db: Session, es_client: Elasticsearch, keyword: str, type: SearchType
) -> List[SearchAllBase]:
    categories = []
    for keyword in split_string_by_comma(keyword):
        if keyword != "":
            keyword = keyword.strip()
            if type == SearchType.industry:
                result = db.execute(
                    """
                    SELECT
                        industries,
                        industries_code,
                        sub_industries,
                        sub_industries_code,
                        CASE
                            WHEN industries ILIKE :keyword_pattern THEN 'industries'
                            WHEN sub_industries ILIKE :keyword_pattern THEN 'sub_industries'
                        END AS field
                    FROM master_categories
                    WHERE industries ILIKE :keyword_pattern
                    OR sub_industries ILIKE :keyword_pattern
                    ORDER BY
                        CASE
                            WHEN industries ILIKE :keyword_pattern THEN 1
                            WHEN sub_industries ILIKE :keyword_pattern THEN 2
                        END;
                """,
                    {"keyword_pattern": f"%{keyword}%"},
                )
                categories_set = set()
                for row in result:
                    if (
                        row.industries not in categories_set
                        and row.field == "industries"
                    ):
                        categories_set.add(row.industries)
                        categories.append(
                            SearchAllBase(
                                field=row.industries, field_code=row.industries_code
                            )
                        )
                    categories.append(
                        SearchAllBase(
                            field=row.industries,
                            field_code=row.industries_code,
                            sub_field=row.sub_industries,
                            sub_field_code=row.sub_industries_code,
                        )
                    )
            elif type == SearchType.location:
                result = db.execute(
                    """
                    SELECT
                        nta_prefecture,
                        nta_prefecture_id,
                        nta_city,
                        nta_city_id,
                        CASE
                            WHEN nta_prefecture ILIKE :keyword_pattern THEN 'nta_prefecture'
                            WHEN nta_city ILIKE :keyword_pattern THEN 'nta_city'
                        END as field
                    FROM
                        master_categories
                    WHERE
                        nta_prefecture ILIKE :keyword_pattern
                    OR
                        nta_city ILIKE :keyword_pattern
                    ORDER BY
                        CASE
                            WHEN nta_prefecture ILIKE :keyword_pattern THEN 1
                            WHEN nta_city ILIKE :keyword_pattern THEN 2
                        END;
                """,
                    {"keyword_pattern": f"%{keyword}%"},
                )
                categories_set = set()
                for row in result:
                    if (
                        row.nta_prefecture not in categories_set
                        and row.field == "nta_prefecture"
                    ):
                        categories_set.add(row.nta_prefecture)
                        categories.append(
                            SearchAllBase(
                                field=row.nta_prefecture,
                                field_code=row.nta_prefecture_id,
                            )
                        )
                    categories.append(
                        SearchAllBase(
                            field=row.nta_prefecture,
                            field_code=row.nta_prefecture_id,
                            sub_field=row.nta_city,
                            sub_field_code=row.nta_city_id,
                        )
                    )
            elif type == SearchType.job_category:
                result = db.execute(
                    """
                    SELECT
                        job_categories,
                        job_categories_code,
                        job_sub_categories,
                        job_sub_categories_code,
                        CASE
                            WHEN job_categories ILIKE :keyword_pattern THEN 'job_categories'
                            WHEN job_sub_categories ILIKE :keyword_pattern THEN 'job_sub_categories'
                        END as field
                    FROM master_categories
                    WHERE job_categories ILIKE :keyword_pattern
                    OR job_sub_categories ILIKE :keyword_pattern
                    ORDER BY
                        CASE
                            WHEN job_categories ILIKE :keyword_pattern THEN 1
                            WHEN job_sub_categories ILIKE :keyword_pattern THEN 2
                        END;
                """,
                    {"keyword_pattern": f"%{keyword}%"},
                )
                categories_set = set()
                for row in result:
                    if (
                        row.job_categories not in categories_set
                        and row.field == "job_categories"
                    ):
                        categories_set.add(row.job_categories)
                        categories.append(
                            SearchAllBase(
                                field=row.job_categories,
                                field_code=row.job_categories_code,
                            )
                        )
                    categories.append(
                        SearchAllBase(
                            field=row.job_categories,
                            field_code=row.job_categories_code,
                            sub_field=row.job_sub_categories,
                            sub_field_code=row.job_sub_categories_code,
                        )
                    )
    seen = set()
    categories_no_duplicates = []
    for x in categories:
        key = x.json()
        if key not in seen:
            seen.add(key)
            categories_no_duplicates.append(x)
    return categories_no_duplicates
