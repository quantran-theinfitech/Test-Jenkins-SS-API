# flake8: noqa: E501

import asyncio
from enum import Enum
from typing import List

from elasticsearch import AsyncElasticsearch, Elasticsearch
from elasticsearch_dsl import Q, Search
from fastapi import BackgroundTasks
from sqlmodel import Session, col, select

from app.api.v1.queries.cross_search_builder import (
    build_person_two_step_query,
    build_press_release_two_step_query,
    build_recruit_two_step_query,
)
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.elasticsearch.press_releases import ESPressRelease
from app.api.v1.schemas.elasticsearch.recruits import ESRecruit
from app.api.v1.schemas.search_cross import (
    SearchCompanyRequest,
    SearchCrossRequest,
    SearchPersonRequest,
    SearchPressReleaseRequest,
    SearchRecruitRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.press_releases.search_press_release_service import (
    build_search_press_release_query,
    make_offset_press_release_data,
)
from app.api.v1.services.redis import RedisService
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from app.models.team_person import TeamPerson
from celery_worker import cache_cross_search_first_steps
from utils import hash_cross_search_query
from utils.custom_sorting import custom_sorting
from utils.extract_domain import (
    extract_full_domain_url,
    normalized_domain_search_companies,
    normalized_sns_url_search_persons,
)
from utils.hash_cross_search_query import hash_cross_search_query
from utils.hash_id import hash_id
from utils.mask_company_data import mask_company_data
from utils.mask_person_data import mask_person_data
from utils.mask_recruit_data import mask_recruit_data


class SearchTarget(Enum):
    COMPANY = "COMPANY"
    PERSON = "PERSON"
    RECRUIT = "RECRUIT"
    PRESS_RELEASE = "PRESS_RELEASE"


class CrossSearchService:
    def __init__(
        self,
        es_client: Elasticsearch,
        db: Session,
        current_user: UserBase,
        es_async_client: AsyncElasticsearch,
        redis_service: RedisService,
        background_task: BackgroundTasks,
    ):
        self.es_client = es_client
        self.db = db
        self.current_user = current_user
        self.es_async_client = es_async_client
        self.redis_service = redis_service
        self.background_task = background_task

    async def search(
        self,
        request: SearchCrossRequest,
        target: SearchTarget,
        current_user: UserBase,
        page: int,
        per_page: int,
        listing_plan_code: PlanCode,
    ):
        search = self._get_es_search(target=target)

        query = await self._build_cross_search_query(
            request, target, current_user, is_statistics=False
        )

        search: Search = search.query(query)
        if (
            all(
                getattr(request, field) in (None, False, [], {}, ())
                for field in request.__fields__
                if field != "is_default_filter"
            )
            and target == SearchTarget.COMPANY
        ) or request.sorting:
            search = custom_sorting(search, request)
        elif target == SearchTarget.RECRUIT:
            search = search.sort(
                {"start_at": {"order": "desc", "missing": "_last"}}, "_score", "_id"
            )
        elif target == SearchTarget.PRESS_RELEASE:
            search = search.sort(
                {"posted_at": {"order": "desc", "missing": "_last"}}, "_score", "_id"
            )
        else:
            search = search.sort("_score", "_id")
        if request and request.is_default_filter:
            search = search.params(request_cache=True)
        size = 0
        if (10000 - ((page - 1) * per_page)) < 15:
            size = 10000 - ((page - 1) * per_page)
        else:
            size = per_page

        data_source = self._get_data_source(target)

        is_track_total_hits = target != SearchTarget.COMPANY

        pagination_param = {
            "size": size,
            "from": (page - 1) * per_page,
            "track_total_hits": is_track_total_hits,
        }

        if data_source:
            pagination_param["_source"] = data_source
        result = search.extra(**pagination_param).execute()["hits"]
        data = result["hits"]._l_
        if is_track_total_hits:
            unlimited_total = result._d_["total"]["value"]
            total = unlimited_total if unlimited_total <= 10000 else 10000
        else:
            total = 0
            unlimited_total = 0

        data = self._mark_offset_result(
            self.db, current_user, target, data, listing_plan_code
        )

        return data, total, unlimited_total

    async def _fetch_companies_ids_streaming(
        self,
        search_condition: SearchCrossRequest,
        current_user: UserBase,
        target: SearchTarget,
    ) -> List[str]:
        self._clear_person_fields_if_needed(search_condition, target)

        cache_key = self._get_cache_key(search_condition)
        cached_data = self.redis_service.get(cache_key)
        if cached_data:
            return cached_data if isinstance(cached_data, list) else cached_data["data"]
        first_page_data = await self._fetch_first_page(
            search_condition, current_user, cache_key
        )

        cache_cross_search_first_steps.apply_async(
            (
                self._build_es_query_dict(search_condition, current_user),
                cache_key,
            )
        )

        # self.background_task.add_task(
        #     self._fetch_remaining_pages_background,
        #     search_condition,
        #     current_user,
        #     cache_key,
        #     first_page_data,
        # )

        return first_page_data

    def _get_cache_key(self, search_condition: SearchCrossRequest) -> str:
        return search_condition.cache_key or hash_cross_search_query(search_condition)

    def _clear_person_fields_if_needed(
        self, search_condition: SearchCrossRequest, target: SearchTarget
    ):
        if target in [SearchTarget.RECRUIT, SearchTarget.PRESS_RELEASE]:
            person_fields = set(SearchPersonRequest.__fields__.keys())
            for field in person_fields:
                setattr(search_condition, field, None)

    async def _fetch_first_page(
        self,
        search_condition: SearchCrossRequest,
        current_user: UserBase,
        cache_key: str,
    ):
        search = self._get_es_search(target=SearchTarget.COMPANY)
        query = self._build_company_query(current_user, search_condition)
        search: Search = search.query(query)
        pagination_param = {
            "size": 100,
            "from": 0,
            "track_total_hits": False,
            "_source": ["corporate_number"],
        }
        result = search.extra(**pagination_param).execute()["hits"]

        data = result["hits"]._l_
        corporate_numbers = [hit["_source"]["corporate_number"] for hit in data]

        cached_data = {
            "data": corporate_numbers,
            "error": False,
            "is_finished": False,
        }
        self.redis_service.set(cache_key, cached_data)

        return corporate_numbers

    def _build_es_query_dict(
        self, search_condition: SearchCrossRequest, current_user: UserBase
    ) -> dict:
        search_query = self._build_company_query(current_user, search_condition)
        search_query = Q("bool", must=search_query)
        return search_query.to_dict()

    def _should_use_two_step_query(
        self, request: SearchCrossRequest, target: SearchTarget
    ) -> bool:
        has_company_filter = (
            self._has_company_filter(request) or target == SearchTarget.COMPANY
        )
        has_person_filter = (
            self._has_person_filter(request) or target == SearchTarget.PERSON
        )
        has_recruit_filter = (
            request.recruit is not None or target == SearchTarget.RECRUIT
        )
        has_press_release_filter = (
            request.new_press_release is not None
            or target == SearchTarget.PRESS_RELEASE
        )

        active_count = 0
        if target == SearchTarget.RECRUIT or target == SearchTarget.PRESS_RELEASE:
            active_count = sum(
                [
                    has_company_filter,
                    has_recruit_filter,
                    has_press_release_filter,
                ]
            )
        else:
            active_count = sum(
                [
                    has_company_filter,
                    has_person_filter,
                    has_recruit_filter,
                    has_press_release_filter,
                ]
            )

        if target == SearchTarget.COMPANY:
            return False

        if active_count < 2:
            return False

        if active_count == 2 and has_company_filter:
            return False

        return True

    def _has_company_filter(self, request: SearchCompanyRequest) -> bool:
        company_fields = set(SearchCompanyRequest.__fields__.keys())
        for field in company_fields:
            if getattr(request, field, None) not in (None, [], {}, ""):
                return True
        return False

    def _has_person_filter(self, request: SearchPersonRequest) -> bool:
        person_fields = set(SearchPersonRequest.__fields__.keys())
        for field in person_fields:
            if getattr(request, field, None) not in (None, [], {}, ""):
                return True
        return False

    def _get_es_search(self, target: SearchTarget):
        if target == SearchTarget.COMPANY:
            return EsCompanyExtend.search(
                using=self.es_client, index=EsCompanyExtend.Index.name
            )
        elif target == SearchTarget.PERSON:
            return ESPersonExtend.search(
                using=self.es_client, index=ESPersonExtend.Index.name
            )
        elif target == SearchTarget.RECRUIT:
            return ESRecruit.search(using=self.es_client, index=ESRecruit.Index.name)
        elif target == SearchTarget.PRESS_RELEASE:
            return ESPressRelease.search(
                using=self.es_client, index=ESPressRelease.Index.name
            )

    def _mark_offset_result(
        self,
        db: Session,
        current_user: UserBase,
        target: SearchTarget,
        data,
        listing_plan_code: PlanCode,
    ):
        if target == SearchTarget.COMPANY:
            companies = [x["_source"] for x in data]
            if listing_plan_code == PlanCode.UNLIMITED:
                for company in companies:
                    company["downloaded_flag"] = True
                    domain_url = extract_full_domain_url(company.get("hp_url"))
                    company["favicon_url"] = (
                        f"{domain_url}/favicon.ico" if domain_url else None
                    )
                return companies
            corporate_numbers = [x["corporate_number"] for x in companies]
            corporate_numbers_downloaded = db.exec(
                select(TeamCompany.corporate_number)
                .where(TeamCompany.team_id == current_user.team_id)
                .where(col(TeamCompany.corporate_number).in_(corporate_numbers))
            ).all()
            return mask_company_data(companies, corporate_numbers_downloaded)

        elif target == SearchTarget.PERSON:
            persons = [x["_source"] for x in data]

            if listing_plan_code == PlanCode.UNLIMITED:
                for person in persons:
                    person["downloaded_flag"] = True
                return persons

            person_uuids = [x["uuid"] for x in persons]
            person_uuids_downloaded = db.exec(
                select(TeamPerson.person_uuid)
                .where(TeamPerson.team_id == current_user.team_id)
                .where(col(TeamPerson.person_uuid).in_(person_uuids))
            ).all()
            return mask_person_data(persons, person_uuids_downloaded)

        elif target == SearchTarget.RECRUIT:
            recruits = [x["_source"] for x in data]
            corporate_numbers_downloaded = db.exec(
                select(TeamCompany.corporate_number).where(
                    TeamCompany.team_id == current_user.team_id,
                )
            ).all()
            for recruit in recruits:
                recruit["id"] = hash_id(recruit.get("id", None))
                company = recruit.get("companies", [{}])[0]
                recruit["company_name"] = company.get("name", None)
                recruit["company_tel"] = company.get("phone", None)
                recruit["contact_email"] = company.get("contact_email", None)
                recruit["job_positions"] = recruit.get("positions", None)
                recruit["job_categories"] = recruit.get("categories", None)
                recruit["holiday_year"] = recruit.get("holiday_year_min", None)
                recruit["company_downloaded_flag"] = (
                    True
                    if (
                        recruit.get("corporate_number", None)
                        in corporate_numbers_downloaded
                    )
                    or listing_plan_code == PlanCode.UNLIMITED
                    else False
                )
                recruit = mask_recruit_data(recruit, corporate_numbers_downloaded)
            return recruits

        elif target == SearchTarget.PRESS_RELEASE:
            press_releases = [x["_source"] for x in data]
            if listing_plan_code == PlanCode.UNLIMITED:
                for data in press_releases:
                    data["company_downloaded_flag"] = True
                    data["contact_email"] = data.get("contact_email")
                    data["hp_url"] = data.get("hp_url")
                    data["contact_form_url"] = data.get("contact_form_url")
                    companies_data = data.get("companies", [])
                    if (
                        isinstance(companies_data, list)
                        and len(companies_data) > 0
                        and isinstance(companies_data[0], dict)
                    ):
                        data.update(companies_data[0])
                        data["company_name"] = companies_data[0].get("name", "")
                    else:
                        data["company_name"] = ""
                return press_releases
            corporate_numbers_downloaded = db.exec(
                select(TeamCompany.corporate_number).where(
                    TeamCompany.team_id == current_user.team_id,
                )
            ).all()
            return make_offset_press_release_data(
                press_releases, corporate_numbers_downloaded
            )

    def _build_company_query(self, current_user: UserBase, request: SearchCrossRequest):
        from app.api.v1.services.companies.build_search_query_by_seach_conditions import (
            build_search_query_by_seach_conditions,
        )

        return build_search_query_by_seach_conditions(
            search_condition=normalized_sns_url_search_persons(
                normalized_domain_search_companies(request)
            ),
            current_user=current_user,
            db=self.db,
        )

    def _build_recruit_query(
        self, request: SearchCrossRequest, db: Session, current_user: UserBase
    ):
        from app.api.v1.queries.recruit import build_es_query as build_recruit_query

        return build_recruit_query(request, self.db, current_user)

    def listing_companies_corporate_number_by_select(
        self,
        db: Session,
        search_condition: SearchCrossRequest,
        es_client: Elasticsearch,
        page: int,
        per_page: int,
        number_of_select: int,
        current_user: UserBase,
    ):
        search = self._get_es_search(target=SearchTarget.COMPANY)

        query = self._build_company_query(current_user, search_condition)
        search: Search = search.query(query).params(request_timeout=30)
        if (
            search_condition == SearchCrossRequest(is_default_filter=True)
            or search_condition.sorting
        ):
            search = custom_sorting(search, search_condition)
        else:
            search = search.sort("_score", "_id")
        if search_condition and search_condition.is_default_filter:
            search = search.params(request_cache=True)

        if (10000 - ((page - 1) * per_page)) < 15:
            10000 - ((page - 1) * per_page)
        else:
            pass
        pagination_param = {
            "size": number_of_select,
            "from": (page - 1) * per_page,
            "track_total_hits": False,
        }

        pagination_param["_source"] = ["corporate_number"]
        result = search.extra(**pagination_param).execute()["hits"]

        data = result["hits"]._l_
        companies = [x["_source"] for x in data]

        corporate_numbers = [x["corporate_number"] for x in companies]

        return corporate_numbers

    def _build_person_query(self, current_user: UserBase, request: SearchPersonRequest):
        from app.api.v1.services.persons.build_search_query_by_search_conditions import (
            build_search_query_by_seach_conditions,
        )

        query = build_search_query_by_seach_conditions(
            search_condition=request, current_user=current_user, db=self.db
        )
        ranking_query = [
            {"exists": {"field": "name", "boost": 2}},
            {"exists": {"field": "linkedin_url", "boost": 2}},
            {"exists": {"field": "role_group_codes", "boost": 1.95}},
            {
                "terms": {
                    "role_group_codes": [
                        "社長",
                        "役員クラス",
                        "経営企画",
                        "責任者クラス",
                        "事業企画/事業開発",
                        "プロジェクトマネジャー",
                        "営業",
                        "営業支援/営業企画",
                    ],
                    "boost": 1.95,
                }
            },
            {"exists": {"field": "wantedly_url", "boost": 1.9}},
            {"exists": {"field": "address", "boost": 1.85}},
            {
                "regexp": {
                    "name": {
                        "value": "[ぁ-んァ-ン一-龥]",
                        "flags": "ALL",
                        "case_insensitive": True,
                        "max_determinized_states": 10000,
                        "rewrite": "constant_score",
                        "boost": 1.8,
                    }
                }
            },
        ]

        return Q("bool", must=query, should=ranking_query, minimum_should_match=0)

    def _get_data_source(self, target: SearchTarget):
        if target == SearchTarget.COMPANY:
            return [
                "name",
                "corporate_number",
                "downloaded_flag",
                "industry_code",
                "president_name",
                "establish_at",
                "listing_market_code",
                "phone",
                "recruit_email",
                "contact_email",
                "hp_url",
                "contact_form_url",
                "original_tags",
            ]

        if target == SearchTarget.PERSON:
            return [
                "downloaded_flag",
                "uuid",
                "name",
                "company_name",
                "corporate_number",
                "role_name",
                "address",
                "contactAddress",
                "linkedin_url",
                "twitter_url",
                "fb_url",
                "wantedly_url",
                "github_url",
            ]

        return []

    async def statistics(
        self,
        request: SearchCrossRequest,
        target: SearchTarget,
        current_user: UserBase,
    ):
        search = self._get_es_search(target=target)

        query = await self._build_cross_search_query(
            request, target, current_user, is_statistics=True
        )

        search: Search = search.query(query)

        if target == SearchTarget.PERSON:
            columns = [
                "linkedin_url",
                "twitter_url",
                "github_url",
                "fb_url",
                "wantedly_url",
            ]
            search.aggs.metric("total", "value_count", field="uuid")
        elif target == SearchTarget.COMPANY:
            columns = [
                "phone",
                "contact_email",
                "recruit_phone",
                "recruit_email",
                "contact_form_url",
                "hp_url",
            ]
            search.aggs.metric("total", "value_count", field="corporate_number")
        for column in columns:
            search.aggs.metric(column, "value_count", field=column)
        if request and request.is_default_filter:
            search = search.params(request_cache=True)

        response = search.extra(
            size=0
        ).execute()  # Data query (.execute(), .count(), ...)

        result = {}

        for column in columns:
            result[column] = response.aggregations[column].value

        result["unlimited_total"] = response.aggregations["total"].value
        result["total"] = (
            result["unlimited_total"] if result["unlimited_total"] < 10000 else 10000
        )
        return result

    async def _build_cross_search_query(
        self,
        request: SearchCrossRequest,
        target: SearchTarget,
        current_user: UserBase,
        is_statistics: bool = False,
    ):
        if target == SearchTarget.COMPANY:
            person_fields = set(SearchPersonRequest.__fields__.keys())
            for field in person_fields:
                setattr(request, field, None)  # set person requests for company by null
        should_use_two_step = self._should_use_two_step_query(
            request=request, target=target
        )
        query = None
        if should_use_two_step:
            corporate_numbers = []
            if is_statistics:
                corporate_numbers = await self._fetch_companies_ids_batch(
                    request, current_user, target
                )
            else:
                if (
                    request.is_companies_unlocked
                    or request.companies_identified
                    or request.company_collections
                ):
                    corporate_numbers = await self._fetch_companies_ids_batch(
                        request, current_user, target
                    )
                else:
                    corporate_numbers = await self._fetch_companies_ids_streaming(
                        request, current_user, target
                    )
            if target == SearchTarget.PERSON:
                query = build_person_two_step_query(
                    self.db, current_user, request, corporate_numbers
                )
            elif target == SearchTarget.RECRUIT:
                query = build_recruit_two_step_query(
                    self.db, request, corporate_numbers, True, current_user
                )
            elif target == SearchTarget.PRESS_RELEASE:
                query = build_press_release_two_step_query(
                    self.db, request, corporate_numbers
                )
        else:
            if target == SearchTarget.COMPANY:
                query = self._build_company_query(current_user, request)
            elif target == SearchTarget.PERSON:
                query = self._build_person_query(current_user, request)
            elif target == SearchTarget.RECRUIT:
                query = self._build_recruit_query(request, self.db, current_user)
            elif target == SearchTarget.PRESS_RELEASE:
                query = build_search_press_release_query(
                    search_condition=request, current_user=current_user, db=self.db
                )
        return query

    async def get_list_person_uuids(
        self,
        request: SearchCrossRequest,
        current_user: UserBase,
        page: int,
        per_page: int,
        max_person_by_company: int,
    ):
        search = self._get_es_search(SearchTarget.PERSON)

        query = await self._build_cross_search_query(
            request, SearchTarget.PERSON, current_user, is_statistics=True
        )

        search = search.query(query).sort("_score", "_id")

        if request and request.is_default_filter:
            search = search.params(request_cache=True)

        corporate_numbers_obj = {}
        added_persons = set()
        list_person = []

        while True:
            size = 0
            if (10000 - ((page - 1) * per_page)) < 15:
                size = 10000 - ((page - 1) * per_page)
            else:
                size = per_page

            if size != per_page:
                return added_persons

            pagination_param = {
                "size": size,
                "from": (page - 1) * per_page,
                "track_total_hits": False,
                "_source": [
                    "uuid",
                    "corporate_number",
                ],
            }
            result = search.extra(**pagination_param).execute()["hits"]
            data = result["hits"]._l_
            if len(data) == 0:
                return added_persons

            page += 1
            persons = [x["_source"] for x in data]

            list_uuids = []
            for person in persons:
                list_uuids.append(person.get("uuid"))
                person["downloaded_flag"] = True

            if max_person_by_company > 0:
                for person in persons:
                    corporate_numbers = person["corporate_number"]
                    person_key = person.get("uuid")

                    if (
                        all(not cn for cn in corporate_numbers)
                        and person_key not in added_persons
                    ):
                        list_person.append(person)
                        added_persons.add(person_key)
                    else:
                        for cn in corporate_numbers:
                            if not cn:
                                continue

                            count = corporate_numbers_obj.setdefault(cn, 0)
                            if (
                                count < max_person_by_company
                                and person_key not in added_persons
                            ):
                                corporate_numbers_obj[cn] += 1
                                list_person.append(person)
                                added_persons.add(person_key)

                    if len(added_persons) == per_page:
                        break

                if len(added_persons) == per_page:
                    return added_persons
            else:
                break

        return list_uuids

    async def _fetch_companies_ids_batch(
        self,
        search_condition: SearchCrossRequest,
        current_user: UserBase,
        target: SearchTarget,
    ) -> List[str]:
        cache_key = search_condition.cache_key
        if not cache_key:
            cache_key = hash_cross_search_query(search_condition)
        cached_data = self.redis_service.get(cache_key)
        if cached_data:
            if cached_data["is_finished"] and not cached_data["error"]:
                return cached_data["data"]

        if target == SearchTarget.RECRUIT or target == SearchTarget.PRESS_RELEASE:
            person_fields = set(SearchPersonRequest.__fields__.keys())
            for field in person_fields:
                setattr(search_condition, field, None)

        mapping_fields = {
            SearchTarget.PERSON: SearchPersonRequest,
            SearchTarget.RECRUIT: SearchRecruitRequest,
            SearchTarget.PRESS_RELEASE: SearchPressReleaseRequest,
        }
        target_fields = set(mapping_fields.get(target).__fields__.keys())
        request = search_condition.copy(deep=True)
        for field in target_fields:
            setattr(request, field, None)  # remove fields search in step 2
        search_query = self._build_company_query(current_user, request)
        search_query = Q("bool", must=search_query)
        query_dict = search_query.to_dict()

        async def execute_async_search(page):
            from_ = page * 1000
            search_body = {
                "query": query_dict,
                "size": 1000,
                "from": from_,
                "track_total_hits": False,
                "_source": ["corporate_number"],
            }

            response = await self.es_async_client.search(
                index=EsCompanyExtend.Index.name,
                body=search_body,
                request_cache=search_condition and search_condition.is_default_filter,
            )
            return response

        all_corporate_numbers = []
        tasks = [execute_async_search(page) for page in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                continue

            if not response or not isinstance(response, dict):
                continue

            hits = response.get("hits", {}).get("hits", [])

            if not hits:
                continue

            companies = [hit["_source"] for hit in hits]
            corporate_numbers = [company["corporate_number"] for company in companies]
            all_corporate_numbers.extend(corporate_numbers)

        return all_corporate_numbers
