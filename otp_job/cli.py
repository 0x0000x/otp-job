from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Sequence

from .client import OTPJobClient
from .console import print_response
from .exceptions import OTPJobAPIError, OTPJobError


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        client = OTPJobClient(
            base_url=args.base_url or _required_env("OTP_JOB_BASE_URL"),
            uid=args.uid or _required_env("OTP_JOB_UID"),
            api_token=args.api_token or _required_env("OTP_JOB_API_TOKEN"),
            timeout=args.timeout,
            retries=args.retries,
            log_level=args.log_level,
        )
        with client:
            response = _run_command(client, args)
        print_response(response, raw=args.raw)
        return 0
    except OTPJobAPIError as exc:
        print(f"API error: {exc.message}", file=sys.stderr)
        if exc.error_code:
            print(f"error_code: {exc.error_code}", file=sys.stderr)
        if exc.suggestion:
            print(f"suggestion: {exc.suggestion}", file=sys.stderr)
        if exc.http_status:
            print(f"http_status: {exc.http_status}", file=sys.stderr)
        return 2
    except (OTPJobError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="otp-job")
    parser.add_argument("--base-url", help="API base URL. Defaults to OTP_JOB_BASE_URL.")
    parser.add_argument("--uid", help="User id. Defaults to OTP_JOB_UID.")
    parser.add_argument("--api-token", help="API token. Defaults to OTP_JOB_API_TOKEN.")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help="Number of retries after failure.",
    )
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None)
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the raw API data envelope payload.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("users-info")

    upload = subparsers.add_parser("numbers-upload")
    upload.add_argument("--project-id", required=True)
    upload.add_argument("--code-type", choices=["sms", "app"], required=True)
    upload.add_argument("--number", action="append", dest="numbers", required=True)

    otp = subparsers.add_parser("otp-upload")
    otp.add_argument("--project-id", required=True)
    otp.add_argument("--number", required=True)
    otp.add_argument("--code", required=True)

    info = subparsers.add_parser("numbers-info")
    info.add_argument("--project-id", required=True)
    info.add_argument("--number", required=True)

    number_list = subparsers.add_parser("numbers-list")
    number_list.add_argument("--project-id", required=True)
    number_list.add_argument("--list-type", choices=["all", "suc"], default="all")
    number_list.add_argument("--page", type=int, default=1)
    number_list.add_argument("--page-size", type=int, default=20)

    return parser


def _run_command(client: OTPJobClient, args: argparse.Namespace):
    if args.command == "status":
        return client.status()
    if args.command == "users-info":
        return client.users_info()
    if args.command == "numbers-upload":
        return client.numbers_upload(
            project_id=args.project_id,
            code_type=args.code_type,
            ccnum_list=args.numbers,
        )
    if args.command == "otp-upload":
        return client.otp_upload(project_id=args.project_id, ccnum=args.number, code=args.code)
    if args.command == "numbers-info":
        return client.numbers_info(project_id=args.project_id, ccnum=args.number)
    if args.command == "numbers-list":
        return client.numbers_list(
            project_id=args.project_id,
            list_type=args.list_type,
            page=args.page,
            page_size=args.page_size,
        )
    raise ValueError(f"Unknown command: {args.command}")


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is required when the matching CLI flag is not provided.")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
