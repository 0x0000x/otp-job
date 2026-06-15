from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Generic, List, Literal, Mapping, Optional, TypeVar


CodeType = Literal["sms", "app"]
ListType = Literal["all", "suc"]
Status = Literal["succ", "err"]

T = TypeVar("T")


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


@dataclass(frozen=True)
class APIResponse(Generic[T]):
    status: str
    data: T
    tips: Optional[str] = None
    raw: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class StatusData:
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
class UserInfoData:
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
class NumberUploadItem:
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


@dataclass(frozen=True)
class NumbersUploadData:
    project_id: str
    uid: str
    code_type: str
    count_succ: int
    count_failed: int
    items: List[NumberUploadItem]

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
class OTPUploadData:
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
class NumberInfoData:
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
class ProjectInfo:
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
class NumbersListData:
    project_info: ProjectInfo
    list_type: str
    page: int
    page_size: int
    total: int
    total_pages: int
    has_more: bool
    items: List[NumberInfoData]

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

