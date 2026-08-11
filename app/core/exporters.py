"""Export scraped data to JSON, CSV, and Excel."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from openpyxl import Workbook


def _flatten(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value) if value is not None else ""


def _normalize_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        if not data:
            return []
        if all(isinstance(item, dict) for item in data):
            return data
        return [{"value": item} for item in data]
    if isinstance(data, dict):
        return [data]
    return [{"value": data}]


def export_json_bytes(data: Any, indent: int = 2) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=indent).encode("utf-8")


def export_json(data: Any, path: str | Path, indent: int = 2) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(export_json_bytes(data, indent=indent))
    return output


def export_csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b""

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _flatten(v) for k, v in row.items()})

    return buffer.getvalue().encode("utf-8")


def export_csv(rows: list[dict[str, Any]], path: str | Path) -> Path:
    if not rows:
        raise ValueError("No rows to export")

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(export_csv_bytes(rows))
    return output


def export_excel_bytes(rows: list[dict[str, Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"

    if not rows:
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    ws.append(fieldnames)
    for row in rows:
        ws.append([_flatten(row.get(k)) for k in fieldnames])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def export_excel(rows: list[dict[str, Any]], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(export_excel_bytes(rows))
    return output


def prepare_export(data: Any, fmt: str) -> tuple[bytes, str, str]:
    """Return (content_bytes, media_type, filename_suffix)."""
    rows = _normalize_rows(data)

    if fmt == "json":
        return export_json_bytes(data), "application/json", "json"
    if fmt == "csv":
        return export_csv_bytes(rows), "text/csv", "csv"
    if fmt in ("xlsx", "excel"):
        return (
            export_excel_bytes(rows),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx",
        )
    raise ValueError(f"Unsupported export format: {fmt}")
