from __future__ import annotations

import json
from typing import Any, Optional

from .models import APIResponse


def print_response(response: APIResponse[Any], *, raw: bool = False) -> None:
    """Pretty-print an API response with colors when Rich is installed."""

    try:
        from rich.console import Console
        from rich.json import JSON
        from rich.table import Table
    except ImportError:
        print(response.to_json(indent=2))
        return

    console = Console()
    style = "green" if response.ok else "red"

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("status", f"[{style}]{response.status}[/{style}]")
    if response.http_status is not None:
        table.add_row("http_status", str(response.http_status))
    if response.elapsed_ms is not None:
        table.add_row("elapsed_ms", f"{response.elapsed_ms:.2f}")
    if response.request_id:
        table.add_row("request_id", response.request_id)
    if response.attempts != 1:
        table.add_row("attempts", str(response.attempts))
    if response.tips:
        table.add_row("tips", f"[yellow]{response.tips}[/yellow]")

    console.print(table)
    payload = response.raw if raw and response.raw is not None else response.data
    console.print(JSON.from_data(_json_ready(payload)))


def format_json(value: Any, *, indent: Optional[int] = 2) -> str:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    return json.dumps(_json_ready(value), ensure_ascii=False, indent=indent)


def _json_ready(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
