import hashlib
from typing import Union


def hash_id(value: Union[str, int]) -> str:
    return hashlib.sha256(str(value).encode()).hexdigest()
