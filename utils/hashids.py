from functools import lru_cache

from hashids import Hashids

from app.config import settings


@lru_cache
def get_hashids() -> Hashids:
    return Hashids(
        salt=settings.HASHIDS_SALT,
        min_length=8,
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
    )
