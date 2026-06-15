# OTP Job Python

A typed, sync and async Python client for the OTP Job API.

`otp-job` wraps every documented OTP Job endpoint, parses the standard API
envelope, returns typed response models, preserves HTTP metadata, supports
retries, offers structured logging, and includes optional console and CLI tools.

Repository: <https://github.com/0x0000x/otp_job>

## Features

- Sync and async clients built on `httpx`.
- Typed dataclass response models for every endpoint.
- `to_dict()` and `to_json()` helpers on responses and data models.
- HTTP metadata on every response: status code, headers, request id, elapsed time,
  retry attempts, and raw JSON.
- API envelope handling for `status`, `tips`, `data`, and `data.error_code`.
- Retry policy for temporary network failures and retryable HTTP status codes.
- Structured logging with API token masking and phone-number masking.
- Optional colored console output powered by `rich`.
- `otp-job` CLI for terminal workflows and automation.
- PEP 561 typing support through `py.typed`.

## Requirements

- Python 3.9 or newer.
- A valid OTP Job API domain, UID, and API token.

The API domain in examples is a placeholder. OTP Job does not expose a universal
public base URL in this package. Use the domain given to you by OTP Job support.

## Getting API Access

To use this client, obtain credentials from OTP Job support:

1. Contact OTP Job online support.
2. Ask for your API base URL, `uid`, and matching `api_token`.
3. Confirm which project ids you can submit numbers to.
4. Keep the API token secret. Do not commit it to Git, paste it into logs, or
   expose it in client-side applications.
5. Test access with `GET /status`, then call a credentialed endpoint such as
   `users_info()`.

Recommended environment variables:

```bash
export OTP_JOB_BASE_URL="https://your-api-domain.example"
export OTP_JOB_UID="10001"
export OTP_JOB_API_TOKEN="your_api_token_here"
```

## Install

From PyPI:

```bash
pip install otp-job
```

With optional console and CLI colors:

```bash
pip install "otp-job[cli]"
```

From GitHub:

```bash
pip install "git+https://github.com/0x0000x/otp_job.git"
```

For local development:

```bash
git clone https://github.com/0x0000x/otp_job.git
cd otp_job
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,cli]"
```

## Quick Start

```python
from otp_job import OTPJobClient

client = OTPJobClient(
    base_url="https://your-api-domain.example",
    uid="10001",
    api_token="your_api_token_here",
)

status = client.status()
print(status.ok)
print(status.http_status)
print(status.elapsed_ms)
print(status.data.healthy)

uploaded = client.numbers_upload(
    project_id="1",
    code_type="sms",
    ccnum_list=["8801712345678", "254712345678"],
)
print(uploaded.data.count_succ, uploaded.data.count_failed)

otp = client.otp_upload(
    project_id="1",
    ccnum="8801712345678",
    code="123456",
)
print(otp.data.queued)
```

Use a context manager when you want deterministic connection cleanup:

```python
from otp_job import OTPJobClient

with OTPJobClient(
    base_url="https://your-api-domain.example",
    uid="10001",
    api_token="your_api_token_here",
) as client:
    response = client.users_info()
    print(response.data.withdrawable_balance)
```

## Async Usage

```python
import asyncio

from otp_job import AsyncOTPJobClient


async def main() -> None:
    async with AsyncOTPJobClient(
        base_url="https://your-api-domain.example",
        uid="10001",
        api_token="your_api_token_here",
    ) as client:
        response = await client.users_info()
        print(response.data.withdrawable_balance)


asyncio.run(main())
```

## Endpoint Map

The client method names stay close to the OTP Job endpoint names.

| API endpoint | Sync method | Async method |
| --- | --- | --- |
| `GET /status` | `client.status()` | `await client.status()` |
| `POST /api/v1/users/info` | `client.users_info()` | `await client.users_info()` |
| `POST /api/v1/projects/{project_id}/numbers/upload` | `client.numbers_upload(...)` | `await client.numbers_upload(...)` |
| `POST /api/v1/projects/{project_id}/otp/upload` | `client.otp_upload(...)` | `await client.otp_upload(...)` |
| `POST /api/v1/projects/{project_id}/numbers/info` | `client.numbers_info(...)` | `await client.numbers_info(...)` |
| `POST /api/v1/projects/{project_id}/numbers/list` | `client.numbers_list(...)` | `await client.numbers_list(...)` |

Convenience aliases are also available:

- `upload_numbers`
- `upload_otp`
- `number_info`
- `number_list`

## API Examples

### Service Status

```python
response = client.status()

print(response.data.healthy)
print(response.data.service)
print(response.data.version)
```

### User Info

```python
response = client.users_info()
data = response.data

print(data.uid)
print(data.withdrawable_balance)
print(data.withdrawable_balance_decimal)
print(data.submitted_number_count)
print(data.successful_registration_count)
```

### Upload Numbers

```python
response = client.numbers_upload(
    project_id="1",
    code_type="sms",
    ccnum_list=["8801712345678", "254712345678"],
)

print(response.data.count_succ)
print(response.data.count_failed)

for item in response.data.items:
    print(item.ccnum, item.success, item.failed_code, item.failed_reason)
```

Rules enforced before sending:

- `code_type` must be `sms` or `app`.
- `ccnum_list` must contain 1 to 20 numbers.

### Upload OTP

```python
response = client.otp_upload(
    project_id="1",
    ccnum="8801712345678",
    code="123456",
)

print(response.data.queued)
print(response.data.code_type)
```

Rules enforced before sending:

- `code` must contain digits only.

### Number Info

```python
response = client.numbers_info(project_id="1", ccnum="8801712345678")
data = response.data

print(data.status_res)
print(data.status_text)
print(data.status_tone)
print(data.action_visible)
print(data.can_submit_otp)
print(data.price_decimal)
```

### Number List

```python
response = client.numbers_list(
    project_id="1",
    list_type="all",
    page=1,
    page_size=20,
)

print(response.data.total)
print(response.data.total_pages)
print(response.data.has_more)

for item in response.data.items:
    print(item.ccnum, item.status_text)
```

Rules enforced before sending:

- `list_type` must be `all` or `suc`.
- `page` must be at least `1`.
- `page_size` must be between `1` and `100`.

## Pagination Helpers

Walk all number-list pages automatically:

```python
for item in client.iter_numbers_list(project_id="1", list_type="all", page_size=100):
    print(item.ccnum, item.status_text)
```

Async:

```python
async for item in client.iter_numbers_list(project_id="1", list_type="all", page_size=100):
    print(item.ccnum, item.status_text)
```

## Response Objects

Every method returns `APIResponse[T]`, where `T` is the typed model for that
endpoint.

```python
response = client.users_info()

print(response.status)       # "succ"
print(response.ok)           # True when API and HTTP status are successful
print(response.tips)         # Usually present only on API errors
print(response.data)         # Typed endpoint model
print(response.raw_json)     # Raw decoded API JSON object
print(response.http_status)  # HTTP status code
print(response.headers)      # Response headers
print(response.request_id)   # x-request-id/request-id/x-correlation-id if present
print(response.elapsed_ms)   # Total request duration in milliseconds
print(response.attempts)     # Number of attempts used
```

Serialize responses and models:

```python
print(response.to_dict())
print(response.to_json(indent=2))
print(response.data.to_dict())
print(response.data.to_json(indent=2))
```

## Error Handling

The OTP Job API returns a standard envelope:

```json
{
  "status": "err",
  "tips": "API token is invalid.",
  "data": {
    "error_code": "invalid_api_token"
  }
}
```

API errors raise `OTPJobAPIError`:

```python
from otp_job import OTPJobAPIError

try:
    client.numbers_info(project_id="1", ccnum="8801712345678")
except OTPJobAPIError as exc:
    print(exc.message)
    print(exc.http_status)
    print(exc.api_status)
    print(exc.error_code)
    print(exc.response_body)
```

Transport failures, invalid JSON, and non-object JSON responses raise
`OTPJobTransportError`.

```python
from otp_job import OTPJobError, OTPJobTransportError

try:
    client.users_info()
except OTPJobTransportError as exc:
    print("Network or response decoding problem:", exc.message)
except OTPJobError as exc:
    print("Any OTP Job client error:", exc)
```

## Retries

Retries are disabled by default. Pass an integer to retry after failed attempts:

```python
client = OTPJobClient(
    base_url="https://your-api-domain.example",
    uid="10001",
    api_token="your_api_token_here",
    retries=3,
)
```

`retries=3` means up to 4 total attempts: the first request plus 3 retries.

For advanced control, use `RetryPolicy`:

```python
from otp_job import RetryPolicy

client = OTPJobClient(
    base_url="https://your-api-domain.example",
    uid="10001",
    api_token="your_api_token_here",
    retries=RetryPolicy(
        attempts=4,
        backoff_factor=0.5,
        status_codes=frozenset({408, 429, 500, 502, 503, 504}),
    ),
)
```

By default, retryable HTTP status codes are:

- `408 Request Timeout`
- `429 Too Many Requests`
- `500 Internal Server Error`
- `502 Bad Gateway`
- `503 Service Unavailable`
- `504 Gateway Timeout`

## Logging

Enable structured logs with `log_level`:

```python
client = OTPJobClient(
    base_url="https://your-api-domain.example",
    uid="10001",
    api_token="your_api_token_here",
    log_level="INFO",
)
```

The client logs request method/path, response status code, elapsed time, retry
attempts, and retry reasons. Sensitive values are masked by default:

- `api_token` becomes `***`.
- Phone numbers are partially masked, for example `880***678`.

Disable masking only in controlled debugging environments:

```python
client = OTPJobClient(
    base_url="https://your-api-domain.example",
    uid="10001",
    api_token="your_api_token_here",
    log_level="DEBUG",
    mask_sensitive=False,
)
```

## Console Output

The `otp_job.console` module gives you a convenient terminal renderer.

Install the optional dependency:

```bash
pip install "otp-job[cli]"
```

Use it from Python:

```python
from otp_job.console import format_json, print_response

response = client.numbers_info(project_id="1", ccnum="8801712345678")

print_response(response)
print_response(response, raw=True)
print(format_json(response.data))
```

When `rich` is installed, output is colorized and JSON is syntax-highlighted.
Without `rich`, `print_response()` falls back to regular JSON output.

## CLI

The package installs an `otp-job` command.

Credentials can be passed with flags:

```bash
otp-job \
  --base-url "https://your-api-domain.example" \
  --uid "10001" \
  --api-token "your_api_token_here" \
  status
```

Or through environment variables:

```bash
export OTP_JOB_BASE_URL="https://your-api-domain.example"
export OTP_JOB_UID="10001"
export OTP_JOB_API_TOKEN="your_api_token_here"

otp-job status
```

### CLI Global Options

| Option | Description |
| --- | --- |
| `--base-url` | API base URL. Defaults to `OTP_JOB_BASE_URL`. |
| `--uid` | OTP Job user id. Defaults to `OTP_JOB_UID`. |
| `--api-token` | OTP Job API token. Defaults to `OTP_JOB_API_TOKEN`. |
| `--timeout` | Request timeout in seconds. Default: `15.0`. |
| `--retries` | Number of retries after the first failed attempt. |
| `--log-level` | One of `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `--raw` | Print the raw API envelope payload instead of only typed data. |

### CLI Commands

Check service status:

```bash
otp-job status
```

Show current user information:

```bash
otp-job users-info
```

Upload one or more numbers:

```bash
otp-job numbers-upload \
  --project-id 1 \
  --code-type sms \
  --number 8801712345678 \
  --number 254712345678
```

Upload an OTP:

```bash
otp-job otp-upload \
  --project-id 1 \
  --number 8801712345678 \
  --code 123456
```

Fetch one number:

```bash
otp-job numbers-info \
  --project-id 1 \
  --number 8801712345678
```

List numbers:

```bash
otp-job numbers-list \
  --project-id 1 \
  --list-type all \
  --page 1 \
  --page-size 100
```

Print the raw API envelope:

```bash
otp-job --raw users-info
```

Enable request logs:

```bash
otp-job --log-level INFO users-info
```

CLI exit codes:

- `0`: success.
- `1`: local configuration, validation, transport, or decoding error.
- `2`: API returned an error envelope or non-success HTTP status.

## Data Models

Main public models:

- `APIResponse[T]`
- `StatusData`
- `UserInfoData`
- `NumbersUploadData`
- `NumberUploadItem`
- `OTPUploadData`
- `NumberInfoData`
- `ProjectInfo`
- `NumbersListData`
- `RetryPolicy`

Useful literals and enums:

- `CodeType`: `sms` or `app`
- `ListType`: `all` or `suc`
- `ResponseStatus`: `succ` or `err`
- `NumberStatusTone`: `success`, `warning`, `error`, or `info`

## Security Notes

- Treat `api_token` as a secret.
- Prefer environment variables or a secret manager.
- Do not store credentials in source code.
- Do not expose credentials in browser apps or mobile apps.
- Keep logging masked in production.
- Rotate credentials with OTP Job support if a token is leaked.

## Development

```bash
git clone https://github.com/0x0000x/otp_job.git
cd otp_job
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,cli]"
```

Run tests:

```bash
python -m pytest
```

Run lint:

```bash
python -m ruff check .
```

Compile check:

```bash
python -m compileall otp_job tests
```

## Project Layout

```text
otp_job/
  __init__.py
  _logging.py
  cli.py
  client.py
  config.py
  console.py
  docs.md
  exceptions.py
  models.py
  py.typed
tests/
  test_client.py
```

## API Documentation

The bundled API notes live in [`otp_job/docs.md`](otp_job/docs.md). They include
the current endpoint list, request body shapes, response examples, and field
notes.

## License

MIT
