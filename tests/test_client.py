from __future__ import annotations

import json

import httpx
import pytest

from otp_job import APIErrorCode, NumberFailureCode, OTPJobAPIError, OTPJobClient
from otp_job._logging import sanitize_payload


def test_response_includes_http_metadata_and_json_helpers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"x-request-id": "req_123"},
            json={
                "status": "succ",
                "data": {"healthy": True, "service": "oj_uapi", "version": "0.1.0"},
            },
        )

    client = OTPJobClient(
        base_url="https://api.example",
        uid="10001",
        api_token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.status()

    assert response.ok is True
    assert response.http_status == 200
    assert response.request_id == "req_123"
    assert response.elapsed_ms is not None
    assert response.data.to_dict() == {
        "healthy": True,
        "service": "oj_uapi",
        "version": "0.1.0",
    }
    assert json.loads(response.to_json())["data"]["healthy"] is True


def test_retries_temporary_status_code() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"status": "err", "tips": "try again", "data": {}})
        return httpx.Response(
            200,
            json={
                "status": "succ",
                "data": {"healthy": True, "service": "oj_uapi", "version": "0.1.0"},
            },
        )

    client = OTPJobClient(
        base_url="https://api.example",
        uid="10001",
        api_token="secret",
        retries=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.status()

    assert calls == 2
    assert response.attempts == 2


def test_api_error_keeps_status_and_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "status": "err",
                "tips": "API token is invalid.",
                "data": {"error_code": "invalid_api_token"},
            },
        )

    client = OTPJobClient(
        base_url="https://api.example",
        uid="10001",
        api_token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OTPJobAPIError) as error:
        client.users_info()

    assert error.value.http_status == 401
    assert error.value.api_status == "err"
    assert error.value.error_code == "invalid_api_token"
    assert error.value.error_code_enum is APIErrorCode.INVALID_API_TOKEN
    assert error.value.suggestion is not None
    assert error.value.error_advice is not None
    assert error.value.error_advice.check_credentials is True
    assert error.value.response_body["tips"] == "API token is invalid."


def test_logging_sanitizes_sensitive_payloads() -> None:
    payload = {
        "uid": "10001",
        "api_token": "secret-token",
        "ccnum": "8801712345678",
        "ccnum_list": ["8801712345678"],
    }

    assert sanitize_payload(payload) == {
        "uid": "10001",
        "api_token": "***",
        "ccnum": "880***678",
        "ccnum_list": ["880***678"],
    }


def test_number_upload_items_include_failure_code_advice() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "succ",
                "data": {
                    "project_id": "1",
                    "uid": "10001",
                    "code_type": "sms",
                    "count_succ": 0,
                    "count_failed": 2,
                    "items": [
                        {
                            "ccnum": "123456",
                            "success": False,
                            "failed_code": "101",
                            "failed_reason": "invalid phone number",
                        },
                        {
                            "ccnum": "8801712345678",
                            "success": False,
                            "failed_code": "202",
                            "failed_reason": "temporarily unavailable",
                        },
                    ],
                },
            },
        )

    client = OTPJobClient(
        base_url="https://api.example",
        uid="10001",
        api_token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.numbers_upload(
        project_id="1",
        code_type="sms",
        ccnum_list=["123456", "8801712345678"],
    )
    invalid, temporary = response.data.items

    assert invalid.failure_code is NumberFailureCode.INVALID_PHONE_NUMBER
    assert invalid.failure_advice is not None
    assert invalid.failure_advice.suggestion == "Check the phone number format and country code."
    assert invalid.retry_later is False
    assert temporary.failure_code is NumberFailureCode.TEMPORARILY_UNAVAILABLE
    assert temporary.failure_advice is not None
    assert temporary.retry_later is True


def test_api_error_advice_uses_documented_error_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "err",
                "tips": "This number does not belong to the current user.",
                "data": {"error_code": "number_owner_mismatch"},
            },
        )

    client = OTPJobClient(
        base_url="https://api.example",
        uid="10001",
        api_token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OTPJobAPIError) as error:
        client.otp_upload(project_id="1", ccnum="8801712345678", code="123456")

    assert error.value.error_code_enum is APIErrorCode.NUMBER_OWNER_MISMATCH
    assert error.value.error_advice is not None
    assert error.value.error_advice.title == "Number owner mismatch"
    assert "uid" in error.value.suggestion


def test_api_error_advice_can_be_inferred_from_tips() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "err",
                "tips": "Number submissions are paused. Please wait a few minutes.",
                "data": {},
            },
        )

    client = OTPJobClient(
        base_url="https://api.example",
        uid="10001",
        api_token="secret",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OTPJobAPIError) as error:
        client.numbers_upload(project_id="1", code_type="sms", ccnum_list=["8801712345678"])

    assert error.value.error_code is None
    assert error.value.error_code_enum is None
    assert error.value.error_advice is not None
    assert error.value.error_advice.code == APIErrorCode.NUMBER_SUBMISSIONS_PAUSED.value
    assert error.value.retry_later is True
