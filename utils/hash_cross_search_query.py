import hashlib
import json

from app.api.v1.schemas.search_cross import SearchCrossRequest


def hash_cross_search_query(query: SearchCrossRequest) -> str:
    return hashlib.sha256(json.dumps(query.dict(), sort_keys=True).encode()).hexdigest()
