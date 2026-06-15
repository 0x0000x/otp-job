from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional, Union


DEFAULT_TIMEOUT = 15.0
DEFAULT_RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    """Retry behavior for temporary transport failures and server responses."""

    attempts: int = 1
    backoff_factor: float = 0.25
    status_codes: FrozenSet[int] = DEFAULT_RETRY_STATUSES

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("retry attempts must be at least 1.")
        if self.backoff_factor < 0:
            raise ValueError("retry backoff_factor cannot be negative.")

    @classmethod
    def disabled(cls) -> "RetryPolicy":
        return cls(attempts=1)

    @classmethod
    def from_value(cls, value: Optional[Union[int, "RetryPolicy"]]) -> "RetryPolicy":
        if isinstance(value, RetryPolicy):
            return value
        if value is None:
            return cls.disabled()
        return cls(attempts=int(value) + 1)

    def delay_for_attempt(self, attempt: int) -> float:
        if attempt <= 1:
            return 0.0
        return self.backoff_factor * (2 ** (attempt - 2))


@dataclass(frozen=True)
class OTPJobConfig:
    """Connection and credential settings for the OTP Job API."""

    base_url: str
    uid: str
    api_token: str
    timeout: float = DEFAULT_TIMEOUT
    retry_policy: RetryPolicy = RetryPolicy()
    log_level: Optional[str] = None
    mask_sensitive: bool = True

    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")
