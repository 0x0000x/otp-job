from __future__ import annotations

from typing import Any, Optional


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

