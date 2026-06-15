from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator, Mapping
from typing import Any, Optional, TypeVar

import httpx

from .config import OTPJobConfig
from .exceptions import OTPJobAPIError, OTPJobTransportError
from .models import (
    APIResponse,
    CodeType,
    ListType,
    NumberInfoData,
    NumbersListData,
    NumbersUploadData,
    OTPUploadData,
    StatusData,
    UserInfoData,
)

T = TypeVar("T")


class _BaseOTPJobClient:
    def __init__(
        self,
        *,
        base_url: str,
        uid: str,
        api_token: str,
        timeout: float = 15.0,
    ) -> None:
        self.config = OTPJobConfig(
            base_url=base_url,
            uid=str(uid),
            api_token=str(api_token),
            timeout=timeout,
        )
        self.base_url = self.config.normalized_base_url()

    def _auth_payload(self, extra: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "uid": self.config.uid,
            "api_token": self.config.api_token,
        }
        if extra:
            payload.update(extra)
        return payload

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _parse_response(
        self,
        response: httpx.Response,
        parser: Callable[[Any], T],
    ) -> APIResponse[T]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise OTPJobTransportError(
                "API response is not valid JSON.",
                http_status=response.status_code,
                response_body=response.text,
            ) from exc

        if not isinstance(payload, Mapping):
            raise OTPJobTransportError(
                "API response JSON is not an object.",
                http_status=response.status_code,
                response_body=payload,
            )

        status = str(payload.get("status", ""))
        tips = payload.get("tips")
        data = payload.get("data", {})
        error_code = self._extract_error_code(data)

        if response.status_code >= 400 or status == "err":
            message = str(tips or response.reason_phrase or "API request failed.")
            raise OTPJobAPIError(
                message,
                http_status=response.status_code,
                api_status=status or None,
                error_code=error_code,
                response_body=payload,
            )

        if status and status != "succ":
            raise OTPJobAPIError(
                f"Unexpected API status: {status}",
                http_status=response.status_code,
                api_status=status,
                error_code=error_code,
                response_body=payload,
            )

        return APIResponse(
            status=status or "succ",
            tips=tips if isinstance(tips, str) else None,
            data=parser(data),
            raw=payload,
        )

    @staticmethod
    def _extract_error_code(data: Any) -> Optional[str]:
        if isinstance(data, Mapping):
            error_code = data.get("error_code")
            if error_code is not None:
                return str(error_code)
        return None

    @staticmethod
    def _validate_project_id(project_id: str) -> str:
        project_id = str(project_id).strip()
        if not project_id:
            raise ValueError("project_id is required.")
        return project_id

    @staticmethod
    def _validate_numbers_upload(code_type: CodeType, ccnum_list: list[str]) -> None:
        if code_type not in ("sms", "app"):
            raise ValueError("code_type must be 'sms' or 'app'.")
        if not ccnum_list:
            raise ValueError("ccnum_list must contain at least one phone number.")
        if len(ccnum_list) > 20:
            raise ValueError("ccnum_list can contain at most 20 phone numbers.")

    @staticmethod
    def _validate_otp(code: str) -> None:
        if not str(code).isdigit():
            raise ValueError("code must contain digits only.")

    @staticmethod
    def _validate_numbers_list(list_type: ListType, page: int, page_size: int) -> None:
        if list_type not in ("all", "suc"):
            raise ValueError("list_type must be 'all' or 'suc'.")
        if page < 1:
            raise ValueError("page must be at least 1.")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100.")


class OTPJobClient(_BaseOTPJobClient):
    """Synchronous client for the OTP Job API."""

    def __init__(
        self,
        *,
        base_url: str,
        uid: str,
        api_token: str,
        timeout: float = 15.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(base_url=base_url, uid=uid, api_token=api_token, timeout=timeout)
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    def __enter__(self) -> "OTPJobClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        parser: Callable[[Any], T],
        json: Optional[Mapping[str, Any]] = None,
    ) -> APIResponse[T]:
        try:
            response = self._client.request(method, self._url(path), json=json)
        except httpx.HTTPError as exc:
            raise OTPJobTransportError(f"API request failed before a response was received: {exc}") from exc
        return self._parse_response(response, parser)

    def status(self) -> APIResponse[StatusData]:
        """GET /status."""
        return self._request("GET", "/status", parser=StatusData.from_mapping)

    def users_info(self) -> APIResponse[UserInfoData]:
        """POST /api/v1/users/info."""
        return self._request(
            "POST",
            "/api/v1/users/info",
            json=self._auth_payload(),
            parser=UserInfoData.from_mapping,
        )

    def numbers_upload(
        self,
        *,
        project_id: str,
        code_type: CodeType,
        ccnum_list: list[str],
    ) -> APIResponse[NumbersUploadData]:
        """POST /api/v1/projects/{project_id}/numbers/upload."""
        project_id = self._validate_project_id(project_id)
        self._validate_numbers_upload(code_type, ccnum_list)
        return self._request(
            "POST",
            f"/api/v1/projects/{project_id}/numbers/upload",
            json=self._auth_payload({"code_type": code_type, "ccnum_list": ccnum_list}),
            parser=NumbersUploadData.from_mapping,
        )

    def otp_upload(
        self,
        *,
        project_id: str,
        ccnum: str,
        code: str,
    ) -> APIResponse[OTPUploadData]:
        """POST /api/v1/projects/{project_id}/otp/upload."""
        project_id = self._validate_project_id(project_id)
        self._validate_otp(code)
        return self._request(
            "POST",
            f"/api/v1/projects/{project_id}/otp/upload",
            json=self._auth_payload({"ccnum": str(ccnum), "code": str(code)}),
            parser=OTPUploadData.from_mapping,
        )

    def numbers_info(self, *, project_id: str, ccnum: str) -> APIResponse[NumberInfoData]:
        """POST /api/v1/projects/{project_id}/numbers/info."""
        project_id = self._validate_project_id(project_id)
        return self._request(
            "POST",
            f"/api/v1/projects/{project_id}/numbers/info",
            json=self._auth_payload({"ccnum": str(ccnum)}),
            parser=NumberInfoData.from_mapping,
        )

    def numbers_list(
        self,
        *,
        project_id: str,
        list_type: ListType = "all",
        page: int = 1,
        page_size: int = 20,
    ) -> APIResponse[NumbersListData]:
        """POST /api/v1/projects/{project_id}/numbers/list."""
        project_id = self._validate_project_id(project_id)
        self._validate_numbers_list(list_type, page, page_size)
        return self._request(
            "POST",
            f"/api/v1/projects/{project_id}/numbers/list",
            json=self._auth_payload(
                {"list_type": list_type, "page": int(page), "page_size": int(page_size)}
            ),
            parser=NumbersListData.from_mapping,
        )

    def iter_numbers_list(
        self,
        *,
        project_id: str,
        list_type: ListType = "all",
        page_size: int = 100,
        start_page: int = 1,
    ) -> Iterator[NumberInfoData]:
        """Iterate every item from /numbers/list until the API reports no more pages."""
        page = start_page
        while True:
            response = self.numbers_list(
                project_id=project_id,
                list_type=list_type,
                page=page,
                page_size=page_size,
            )
            yield from response.data.items
            if not response.data.has_more:
                break
            page += 1

    upload_numbers = numbers_upload
    upload_otp = otp_upload
    number_info = numbers_info
    number_list = numbers_list


class AsyncOTPJobClient(_BaseOTPJobClient):
    """Asynchronous client for the OTP Job API."""

    def __init__(
        self,
        *,
        base_url: str,
        uid: str,
        api_token: str,
        timeout: float = 15.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(base_url=base_url, uid=uid, api_token=api_token, timeout=timeout)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    async def __aenter__(self) -> "AsyncOTPJobClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        parser: Callable[[Any], T],
        json: Optional[Mapping[str, Any]] = None,
    ) -> APIResponse[T]:
        try:
            response = await self._client.request(method, self._url(path), json=json)
        except httpx.HTTPError as exc:
            raise OTPJobTransportError(f"API request failed before a response was received: {exc}") from exc
        return self._parse_response(response, parser)

    async def status(self) -> APIResponse[StatusData]:
        """GET /status."""
        return await self._request("GET", "/status", parser=StatusData.from_mapping)

    async def users_info(self) -> APIResponse[UserInfoData]:
        """POST /api/v1/users/info."""
        return await self._request(
            "POST",
            "/api/v1/users/info",
            json=self._auth_payload(),
            parser=UserInfoData.from_mapping,
        )

    async def numbers_upload(
        self,
        *,
        project_id: str,
        code_type: CodeType,
        ccnum_list: list[str],
    ) -> APIResponse[NumbersUploadData]:
        """POST /api/v1/projects/{project_id}/numbers/upload."""
        project_id = self._validate_project_id(project_id)
        self._validate_numbers_upload(code_type, ccnum_list)
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/numbers/upload",
            json=self._auth_payload({"code_type": code_type, "ccnum_list": ccnum_list}),
            parser=NumbersUploadData.from_mapping,
        )

    async def otp_upload(
        self,
        *,
        project_id: str,
        ccnum: str,
        code: str,
    ) -> APIResponse[OTPUploadData]:
        """POST /api/v1/projects/{project_id}/otp/upload."""
        project_id = self._validate_project_id(project_id)
        self._validate_otp(code)
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/otp/upload",
            json=self._auth_payload({"ccnum": str(ccnum), "code": str(code)}),
            parser=OTPUploadData.from_mapping,
        )

    async def numbers_info(self, *, project_id: str, ccnum: str) -> APIResponse[NumberInfoData]:
        """POST /api/v1/projects/{project_id}/numbers/info."""
        project_id = self._validate_project_id(project_id)
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/numbers/info",
            json=self._auth_payload({"ccnum": str(ccnum)}),
            parser=NumberInfoData.from_mapping,
        )

    async def numbers_list(
        self,
        *,
        project_id: str,
        list_type: ListType = "all",
        page: int = 1,
        page_size: int = 20,
    ) -> APIResponse[NumbersListData]:
        """POST /api/v1/projects/{project_id}/numbers/list."""
        project_id = self._validate_project_id(project_id)
        self._validate_numbers_list(list_type, page, page_size)
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/numbers/list",
            json=self._auth_payload(
                {"list_type": list_type, "page": int(page), "page_size": int(page_size)}
            ),
            parser=NumbersListData.from_mapping,
        )

    async def iter_numbers_list(
        self,
        *,
        project_id: str,
        list_type: ListType = "all",
        page_size: int = 100,
        start_page: int = 1,
    ) -> AsyncIterator[NumberInfoData]:
        """Iterate every item from /numbers/list until the API reports no more pages."""
        page = start_page
        while True:
            response = await self.numbers_list(
                project_id=project_id,
                list_type=list_type,
                page=page,
                page_size=page_size,
            )
            for item in response.data.items:
                yield item
            if not response.data.has_more:
                break
            page += 1

    upload_numbers = numbers_upload
    upload_otp = otp_upload
    number_info = numbers_info
    number_list = numbers_list
