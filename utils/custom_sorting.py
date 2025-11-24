from typing import Optional

from elasticsearch_dsl import Search

from app.api.v1.schemas.search_cross import (
    SearchCrossRequest,
    SortField,
    Sorting,
    SortOrder,
)


def custom_sorting(
    search: Search, search_condition: Optional[SearchCrossRequest] = None
) -> Search:
    try:
        if not search_condition:
            search_condition = SearchCrossRequest()
        if not search_condition.sorting:
            search_condition.sorting = Sorting()
        field = search_condition.sorting.field
        order_val = search_condition.sorting.order

        if not field:
            field = SortField.EMPLOYEES_COUNT

        if not order_val:
            order_val = SortOrder.DESC

        field_name = field.value.lower()
        order = "desc" if order_val == SortOrder.DESC else "asc"
        search = search.sort(
            {field_name: {"order": order, "missing": "_last"}}, "_score", "_id"
        )
    except Exception:
        search = search.sort("_score", "_id")
    return search
