from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, Literal, Mapping, Optional, TypeVar


CodeType = Literal["sms", "app"]
ListType = Literal["all", "suc"]
Status = Literal["succ", "err"]

T = TypeVar("T")


class SerializableModel:
    """Mixin for JSON-friendly dataclass models."""

    def to_dict(self) -> dict[str, Any]:
        return _to_plain(self)

    def to_json(self, *, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class ResponseStatus(str, Enum):
    SUCCESS = "succ"
    ERROR = "err"


class NumberStatusTone(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class NumberFailureCode(str, Enum):
    INVALID_PHONE_NUMBER = "101"
    USED_SUCCESSFULLY_WITHIN_30_DAYS = "102"
    STILL_IN_PROGRESS = "103"
    COUNTRY_DEMAND_SATISFIED = "104"
    UNSUPPORTED_COUNTRY_OR_OTP_TYPE = "105"
    TEMPORARILY_UNAVAILABLE = "202"


class APIErrorCode(str, Enum):
    INVALID_API_TOKEN = "invalid_api_token"
    NUMBER_OWNER_MISMATCH = "number_owner_mismatch"
    NUMBER_NOT_FOUND = "number_not_found"
    OTP_FORMAT_ERROR = "otp_format_error"
    OTP_STATUS_NOT_ALLOWED = "otp_status_not_allowed"
    NUMBER_SUBMISSIONS_PAUSED = "number_submissions_paused"
    PROJECT_CLOSED = "project_closed"
    INVALID_PROJECT_ID = "invalid_project_id"
    INVALID_JSON_FORMAT = "invalid_json_format"
    INVALID_UID = "invalid_uid"
    PAGE_SIZE_TOO_LARGE = "page_size_too_large"


@dataclass(frozen=True)
class FailureAdvice(SerializableModel):
    code: str
    title: str
    suggestion: str
    retry_later: bool = False


@dataclass(frozen=True)
class APIErrorAdvice(SerializableModel):
    code: str
    title: str
    suggestion: str
    retry_later: bool = False
    check_credentials: bool = False


NUMBER_FAILURE_ADVICE: Mapping[str, FailureAdvice] = {
    NumberFailureCode.INVALID_PHONE_NUMBER.value: FailureAdvice(
        code=NumberFailureCode.INVALID_PHONE_NUMBER.value,
        title="Invalid phone number",
        suggestion="Check the phone number format and country code.",
    ),
    NumberFailureCode.USED_SUCCESSFULLY_WITHIN_30_DAYS.value: FailureAdvice(
        code=NumberFailureCode.USED_SUCCESSFULLY_WITHIN_30_DAYS.value,
        title="Number already used successfully within 30 days",
        suggestion="Use a different phone number.",
    ),
    NumberFailureCode.STILL_IN_PROGRESS.value: FailureAdvice(
        code=NumberFailureCode.STILL_IN_PROGRESS.value,
        title="Number still in progress",
        suggestion="Retry later.",
        retry_later=True,
    ),
    NumberFailureCode.COUNTRY_DEMAND_SATISFIED.value: FailureAdvice(
        code=NumberFailureCode.COUNTRY_DEMAND_SATISFIED.value,
        title="Country demand is currently satisfied",
        suggestion="Try another country or wait for demand to reopen.",
    ),
    NumberFailureCode.UNSUPPORTED_COUNTRY_OR_OTP_TYPE.value: FailureAdvice(
        code=NumberFailureCode.UNSUPPORTED_COUNTRY_OR_OTP_TYPE.value,
        title="Unsupported country or OTP type",
        suggestion="Try another country or OTP type.",
    ),
    NumberFailureCode.TEMPORARILY_UNAVAILABLE.value: FailureAdvice(
        code=NumberFailureCode.TEMPORARILY_UNAVAILABLE.value,
        title="Number temporarily unavailable",
        suggestion="Retry later.",
        retry_later=True,
    ),
}

API_ERROR_ADVICE: Mapping[str, APIErrorAdvice] = {
    APIErrorCode.INVALID_API_TOKEN.value: APIErrorAdvice(
        code=APIErrorCode.INVALID_API_TOKEN.value,
        title="Invalid API token",
        suggestion="Confirm that uid and api_token match the credentials from OTP Job support.",
        check_credentials=True,
    ),
    APIErrorCode.NUMBER_OWNER_MISMATCH.value: APIErrorAdvice(
        code=APIErrorCode.NUMBER_OWNER_MISMATCH.value,
        title="Number owner mismatch",
        suggestion="Confirm that the request uid matches the user that uploaded the number.",
        check_credentials=True,
    ),
    APIErrorCode.NUMBER_NOT_FOUND.value: APIErrorAdvice(
        code=APIErrorCode.NUMBER_NOT_FOUND.value,
        title="Number does not exist",
        suggestion="Confirm that the number was uploaded successfully before this request.",
    ),
    APIErrorCode.OTP_FORMAT_ERROR.value: APIErrorAdvice(
        code=APIErrorCode.OTP_FORMAT_ERROR.value,
        title="OTP format error",
        suggestion="Confirm that code contains digits only.",
    ),
    APIErrorCode.OTP_STATUS_NOT_ALLOWED.value: APIErrorAdvice(
        code=APIErrorCode.OTP_STATUS_NOT_ALLOWED.value,
        title="Current status does not allow OTP submission",
        suggestion=(
            "Query the current number status first. "
            "OTP can be submitted only for status 1 or 6."
        ),
    ),
    APIErrorCode.NUMBER_SUBMISSIONS_PAUSED.value: APIErrorAdvice(
        code=APIErrorCode.NUMBER_SUBMISSIONS_PAUSED.value,
        title="Number submissions are paused",
        suggestion="Wait a few minutes before uploading numbers again.",
        retry_later=True,
    ),
    APIErrorCode.PROJECT_CLOSED.value: APIErrorAdvice(
        code=APIErrorCode.PROJECT_CLOSED.value,
        title="Project is closed",
        suggestion="Confirm the project_id and whether this project is open for submissions.",
    ),
    APIErrorCode.INVALID_PROJECT_ID.value: APIErrorAdvice(
        code=APIErrorCode.INVALID_PROJECT_ID.value,
        title="Invalid project id",
        suggestion="Confirm project_id with OTP Job support or your project dashboard.",
    ),
    APIErrorCode.INVALID_JSON_FORMAT.value: APIErrorAdvice(
        code=APIErrorCode.INVALID_JSON_FORMAT.value,
        title="Invalid JSON format",
        suggestion="Confirm that the request body is valid JSON and matches the documented schema.",
    ),
    APIErrorCode.INVALID_UID.value: APIErrorAdvice(
        code=APIErrorCode.INVALID_UID.value,
        title="Invalid uid",
        suggestion="Confirm that uid is correct and belongs to the API token being used.",
        check_credentials=True,
    ),
    APIErrorCode.PAGE_SIZE_TOO_LARGE.value: APIErrorAdvice(
        code=APIErrorCode.PAGE_SIZE_TOO_LARGE.value,
        title="Page size too large",
        suggestion="Use page_size between 1 and 100.",
    ),
}

_API_ERROR_TIP_PATTERNS: tuple[tuple[str, APIErrorCode], ...] = (
    ("api token", APIErrorCode.INVALID_API_TOKEN),
    ("number submissions are paused", APIErrorCode.NUMBER_SUBMISSIONS_PAUSED),
    ("number does not belong", APIErrorCode.NUMBER_OWNER_MISMATCH),
    ("owner", APIErrorCode.NUMBER_OWNER_MISMATCH),
    ("number does not exist", APIErrorCode.NUMBER_NOT_FOUND),
    ("not exist", APIErrorCode.NUMBER_NOT_FOUND),
    ("otp format", APIErrorCode.OTP_FORMAT_ERROR),
    ("code format", APIErrorCode.OTP_FORMAT_ERROR),
    ("digits only", APIErrorCode.OTP_FORMAT_ERROR),
    ("status does not allow", APIErrorCode.OTP_STATUS_NOT_ALLOWED),
    ("does not allow otp", APIErrorCode.OTP_STATUS_NOT_ALLOWED),
    ("project is closed", APIErrorCode.PROJECT_CLOSED),
    ("project closed", APIErrorCode.PROJECT_CLOSED),
    ("project_id", APIErrorCode.INVALID_PROJECT_ID),
    ("project id", APIErrorCode.INVALID_PROJECT_ID),
    ("json", APIErrorCode.INVALID_JSON_FORMAT),
    ("uid", APIErrorCode.INVALID_UID),
    ("page_size", APIErrorCode.PAGE_SIZE_TOO_LARGE),
    ("page size", APIErrorCode.PAGE_SIZE_TOO_LARGE),
)


def get_api_error_advice(
    error_code: Optional[str] = None,
    tips: Optional[str] = None,
) -> Optional[APIErrorAdvice]:
    if error_code:
        advice = API_ERROR_ADVICE.get(error_code)
        if advice:
            return advice

    normalized_tips = (tips or "").strip().lower()
    for pattern, code in _API_ERROR_TIP_PATTERNS:
        if pattern in normalized_tips:
            return API_ERROR_ADVICE[code.value]
    return None


def _as_dict(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return default


def _to_plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_plain(getattr(value, field.name))
            for field in dataclasses.fields(value)
            if field.repr or hasattr(value, field.name)
        }
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class APIResponse(Generic[T], SerializableModel):
    status: str
    data: T
    tips: Optional[str] = None
    raw: Optional[Mapping[str, Any]] = None
    http_status: Optional[int] = None
    headers: Mapping[str, str] = dataclasses.field(default_factory=dict)
    elapsed_ms: Optional[float] = None
    request_id: Optional[str] = None
    attempts: int = 1

    @property
    def ok(self) -> bool:
        return self.status == ResponseStatus.SUCCESS.value and (
            self.http_status is None or self.http_status < 400
        )

    @property
    def raw_json(self) -> Optional[Mapping[str, Any]]:
        return self.raw

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "tips": self.tips,
            "data": _to_plain(self.data),
            "http_status": self.http_status,
            "headers": dict(self.headers),
            "elapsed_ms": self.elapsed_ms,
            "request_id": self.request_id,
            "attempts": self.attempts,
            "raw": _to_plain(self.raw),
        }


@dataclass(frozen=True)
class StatusData(SerializableModel):
    healthy: bool
    service: str
    version: str

    @classmethod
    def from_mapping(cls, value: Any) -> "StatusData":
        data = _as_dict(value)
        return cls(
            healthy=_bool(data.get("healthy")),
            service=_str(data.get("service")),
            version=_str(data.get("version")),
        )


@dataclass(frozen=True)
class UserInfoData(SerializableModel):
    uid: str
    withdrawable_balance: str
    withdrawing_balance: str
    withdrawn_balance: str
    total_income: str
    work_income: str
    promotion_income: str
    submitted_number_count: int
    submitted_otp_count: int
    successful_registration_count: int

    @classmethod
    def from_mapping(cls, value: Any) -> "UserInfoData":
        data = _as_dict(value)
        return cls(
            uid=_str(data.get("uid")),
            withdrawable_balance=_str(data.get("withdrawable_balance"), "0.0000"),
            withdrawing_balance=_str(data.get("withdrawing_balance"), "0.0000"),
            withdrawn_balance=_str(data.get("withdrawn_balance"), "0.0000"),
            total_income=_str(data.get("total_income"), "0.0000"),
            work_income=_str(data.get("work_income"), "0.0000"),
            promotion_income=_str(data.get("promotion_income"), "0.0000"),
            submitted_number_count=_int(data.get("submitted_number_count")),
            submitted_otp_count=_int(data.get("submitted_otp_count")),
            successful_registration_count=_int(data.get("successful_registration_count")),
        )

    @property
    def withdrawable_balance_decimal(self) -> Decimal:
        return Decimal(self.withdrawable_balance)


@dataclass(frozen=True)
class NumberUploadItem(SerializableModel):
    ccnum: str
    success: bool
    failed_code: str
    failed_reason: str

    @classmethod
    def from_mapping(cls, value: Any) -> "NumberUploadItem":
        data = _as_dict(value)
        return cls(
            ccnum=_str(data.get("ccnum")),
            success=_bool(data.get("success")),
            failed_code=_str(data.get("failed_code")),
            failed_reason=_str(data.get("failed_reason")),
        )

    @property
    def failure_code(self) -> Optional[NumberFailureCode]:
        try:
            return NumberFailureCode(self.failed_code)
        except ValueError:
            return None

    @property
    def failure_advice(self) -> Optional[FailureAdvice]:
        return NUMBER_FAILURE_ADVICE.get(self.failed_code)

    @property
    def retry_later(self) -> bool:
        advice = self.failure_advice
        return bool(advice and advice.retry_later)


@dataclass(frozen=True)
class NumbersUploadData(SerializableModel):
    project_id: str
    uid: str
    code_type: str
    count_succ: int
    count_failed: int
    items: list[NumberUploadItem]

    @classmethod
    def from_mapping(cls, value: Any) -> "NumbersUploadData":
        data = _as_dict(value)
        return cls(
            project_id=_str(data.get("project_id")),
            uid=_str(data.get("uid")),
            code_type=_str(data.get("code_type")),
            count_succ=_int(data.get("count_succ")),
            count_failed=_int(data.get("count_failed")),
            items=[NumberUploadItem.from_mapping(item) for item in _as_list(data.get("items"))],
        )


@dataclass(frozen=True)
class OTPUploadData(SerializableModel):
    project_id: str
    ccnum: str
    code: str
    code_type: str
    queued: bool

    @classmethod
    def from_mapping(cls, value: Any) -> "OTPUploadData":
        data = _as_dict(value)
        return cls(
            project_id=_str(data.get("project_id")),
            ccnum=_str(data.get("ccnum")),
            code=_str(data.get("code")),
            code_type=_str(data.get("code_type")),
            queued=_bool(data.get("queued")),
        )


@dataclass(frozen=True)
class NumberInfoData(SerializableModel):
    project_id: str
    uid: str
    ccnum: str
    country_code: str
    price: str
    code_type: str
    status_res: str
    status_text: str
    status_tone: str
    action_visible: bool

    @classmethod
    def from_mapping(cls, value: Any) -> "NumberInfoData":
        data = _as_dict(value)
        return cls(
            project_id=_str(data.get("project_id")),
            uid=_str(data.get("uid")),
            ccnum=_str(data.get("ccnum")),
            country_code=_str(data.get("country_code")),
            price=_str(data.get("price"), "0.0000"),
            code_type=_str(data.get("code_type")),
            status_res=_str(data.get("status_res")),
            status_text=_str(data.get("status_text")),
            status_tone=_str(data.get("status_tone")),
            action_visible=_bool(data.get("action_visible")),
        )

    @property
    def country_code_upper(self) -> str:
        return self.country_code.upper()

    @property
    def can_submit_otp(self) -> bool:
        return self.status_res in {"1", "6"}

    @property
    def price_decimal(self) -> Decimal:
        return Decimal(self.price)


@dataclass(frozen=True)
class ProjectInfo(SerializableModel):
    project_id: str
    project_name: str
    project_income: str

    @classmethod
    def from_mapping(cls, value: Any) -> "ProjectInfo":
        data = _as_dict(value)
        return cls(
            project_id=_str(data.get("project_id")),
            project_name=_str(data.get("project_name")),
            project_income=_str(data.get("project_income"), "0.0000"),
        )

    @property
    def project_income_decimal(self) -> Decimal:
        return Decimal(self.project_income)


@dataclass(frozen=True)
class NumbersListData(SerializableModel):
    project_info: ProjectInfo
    list_type: str
    page: int
    page_size: int
    total: int
    total_pages: int
    has_more: bool
    items: list[NumberInfoData]

    @classmethod
    def from_mapping(cls, value: Any) -> "NumbersListData":
        data = _as_dict(value)
        return cls(
            project_info=ProjectInfo.from_mapping(data.get("project_info")),
            list_type=_str(data.get("list_type")),
            page=_int(data.get("page")),
            page_size=_int(data.get("page_size")),
            total=_int(data.get("total")),
            total_pages=_int(data.get("total_pages")),
            has_more=_bool(data.get("has_more")),
            items=[NumberInfoData.from_mapping(item) for item in _as_list(data.get("items"))],
        )
