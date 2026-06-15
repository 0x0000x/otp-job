from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Optional


LOGGER_NAME = "otp_job"
SENSITIVE_KEYS = {"api_token", "token", "authorization", "password", "secret"}


def get_logger(level: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if level:
        logger.setLevel(_level_value(level))
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
            logger.addHandler(handler)
    return logger


def _level_value(level: str) -> int:
    value = getattr(logging, level.upper(), None)
    if not isinstance(value, int):
        raise ValueError(f"Unknown log level: {level}")
    return value


def sanitize_payload(value: Any, *, mask_sensitive: bool = True) -> Any:
    if not mask_sensitive:
        return value
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if key_str.lower() in SENSITIVE_KEYS:
                sanitized[key_str] = "***"
            elif key_str == "ccnum":
                sanitized[key_str] = mask_phone(str(item))
            elif key_str == "ccnum_list" and isinstance(item, list):
                sanitized[key_str] = [mask_phone(str(number)) for number in item]
            else:
                sanitized[key_str] = sanitize_payload(item, mask_sensitive=mask_sensitive)
        return sanitized
    if isinstance(value, list):
        return [sanitize_payload(item, mask_sensitive=mask_sensitive) for item in value]
    return value


def mask_phone(value: str) -> str:
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}***{value[-3:]}"
