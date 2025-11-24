from typing import Any

from fastapi import HTTPException


class BadRequestException(HTTPException):
    def __init__(self, detail: Any = "Bad Request") -> None:
        super().__init__(400, detail)


class UnauthorizedException(HTTPException):
    def __init__(
        self,
        detail: Any = "Unauthorized",
        headers: Any = {"WWW-Authenticate": "Bearer"},
    ) -> None:
        super().__init__(401, detail, headers)


class NotFoundException(HTTPException):
    def __init__(self, detail: Any = "Not found") -> None:
        super().__init__(404, detail)


class InternalException(HTTPException):
    def __init__(self, detail: Any = "Internal Server Error") -> None:
        super().__init__(500, detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: Any = "Forbidden") -> None:
        super().__init__(403, detail)


class NoContentException(HTTPException):
    def __init__(self, detail: Any = "No content") -> None:
        super().__init__(204, detail)


class ConflictException(HTTPException):
    def __init__(self, detail: Any = "Conflict") -> None:
        super().__init__(409, detail)


class PaymentRequiredException(HTTPException):
    def __init__(self, detail: Any = "Payment Required") -> None:
        super().__init__(402, detail)


class TooManyRequestsException(HTTPException):
    def __init__(self, detail: Any = "Too Many Requests") -> None:
        super().__init__(429, detail)
