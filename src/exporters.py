"""Export scraped data to JSON and CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def export_json(data: Any, path: str | Path, indent: int = 2) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    return output


def export_csv(rows: list[dict], path: str | Path) -> Path:
    if not rows:
        raise ValueError("No rows to export")

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flat = {k: _flatten(v) for k, v in row.items()}
            writer.writerow(flat)

    return output


def _flatten(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value) if value is not None else ""
