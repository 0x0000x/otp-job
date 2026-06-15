from __future__ import annotations

from typing import Any, Optional

from .models import APIErrorCode, get_api_error_advice


class OTPJobError(Exception):
    """Base exception for this package."""


class OTPJobAPIError(OTPJobError):
    """Raised when the API returns an error envelope or a non-success HTTP status."""

    def __init__(
        self,
        message: str,
        *,
        http_status: Optional[int] = None,
        api_status: Optional[str] = None,
        error_code: Optional[str] = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.api_status = api_status
        self.error_code = error_code
        self.response_body = response_body
        self.error_advice = get_api_error_advice(error_code, message)

    @property
    def error_code_enum(self) -> Optional[APIErrorCode]:
        if self.error_code is None:
            return None
        try:
            return APIErrorCode(self.error_code)
        except ValueError:
            return None

    @property
    def retry_later(self) -> bool:
        return bool(self.error_advice and self.error_advice.retry_later)

    @property
    def suggestion(self) -> Optional[str]:
        if self.error_advice is None:
            return None
        return self.error_advice.suggestion


class OTPJobTransportError(OTPJobError):
    """Raised when the request cannot be sent or the response cannot be decoded."""

    def __init__(
        self,
        message: str,
        *,
        http_status: Optional[int] = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.response_body = response_body
