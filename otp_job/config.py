from __future__ import annotations

from dataclasses import dataclass


DEFAULT_TIMEOUT = 15.0


@dataclass(frozen=True)
class OTPJobConfig:
    """Connection and credential settings for the OTP Job API."""

    base_url: str
    uid: str
    api_token: str
    timeout: float = DEFAULT_TIMEOUT

    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")

