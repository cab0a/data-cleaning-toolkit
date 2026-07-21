"""Conservative schema suggestions with per-column evidence."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import CsvTable
from .reporting import sha256_file


_INTEGER_PATTERN = re.compile(r"[+-]?\d+")
_LEADING_ZERO_PATTERN = re.compile(r"[+-]?0\d+")
_TEXTUAL_BOOLEANS = {"true", "false", "yes", "no", "y", "n"}


def _is_boolean(value: str) -> bool:
    return value.casefold() in _TEXTUAL_BOOLEANS


def _is_integer(value: str) -> bool:
    return (
        _INTEGER_PATTERN.fullmatch(value) is not None
        and _LEADING_ZERO_PATTERN.fullmatch(value) is None
    )


def _is_decimal(value: str) -> bool:
    if _LEADING_ZERO_PATTERN.fullmatch(value) is not None:
        return False
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return False
    return parsed.is_finite()


def _date_parser(date_format: str) -> Callable[[str], bool]:
    def parse(value: str) -> bool:
        try:
            datetime.strptime(value, date_format)
        except ValueError:
            return False
        return True

    return parse


def _coverage(values: list[str], predicate: Callable[[str], bool]) -> float:
    if not values:
        return 0.0
    return round(sum(predicate(value) for value in values) / len(values), 6)


def suggest_schema(
    table: CsvTable,
    *,
    date_format: str = "%Y-%m-%d",
) -> dict[str, Any]:
    """Return a reviewable schema candidate and evidence for every column."""

    try:
        example = datetime(2000, 1, 2).strftime(date_format)
        datetime.strptime(example, date_format)
    except ValueError as exc:
        raise ValueError(f"Invalid date format: {date_format}") from exc

    date_matches = _date_parser(date_format)
    suggested_columns: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []

    for header in table.headers:
        raw_values = [row.values[header] for row in table.rows]
        stripped_values = [value.strip() for value in raw_values]
        non_empty = [value for value in stripped_values if value != ""]
        empty_cells = len(stripped_values) - len(non_empty)
        whitespace_changes = sum(
            raw != stripped for raw, stripped in zip(raw_values, stripped_values)
        )
        coverage = {
            "boolean": _coverage(non_empty, _is_boolean),
            "integer": _coverage(non_empty, _is_integer),
            "decimal": _coverage(non_empty, _is_decimal),
            "date": _coverage(non_empty, date_matches),
        }
        suggested_type = "string"
        for candidate in ("boolean", "integer", "decimal", "date"):
            if coverage[candidate] == 1.0:
                suggested_type = candidate
                break

        required = bool(raw_values) and empty_cells == 0
        rule: dict[str, Any] = {
            "type": suggested_type,
            "required": required,
        }
        if whitespace_changes:
            rule["strip"] = True
        if suggested_type == "date":
            rule["input_format"] = date_format
            rule["output_format"] = date_format
        suggested_columns[header] = rule
        evidence.append(
            {
                "name": header,
                "non_empty_cells": len(non_empty),
                "empty_cells": empty_cells,
                "whitespace_changes": whitespace_changes,
                "leading_zero_values": sum(
                    _LEADING_ZERO_PATTERN.fullmatch(value) is not None
                    for value in non_empty
                ),
                "suggested_type": suggested_type,
                "required": required,
                "parse_coverage": coverage,
            }
        )

    return {
        "report_version": 1,
        "source": table.source.as_posix(),
        "source_sha256": sha256_file(table.source),
        "input_rows": len(table.rows),
        "column_count": len(table.headers),
        "malformed_rows": sum(
            issue.code == "ROW_WIDTH_MISMATCH" for issue in table.issues
        ),
        "date_format": date_format,
        "suggested_schema": {
            "version": 1,
            "unknown_columns": "error",
            "invalid_rows": "drop",
            "deduplicate_by": [],
            "columns": suggested_columns,
        },
        "columns": evidence,
        "issues": [issue.as_dict() for issue in table.issues],
    }
